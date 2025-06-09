from app.core.celery_config.celery_app import celery_app
import logging
from datetime import datetime
import asyncio
import socketio
from app.core.config import settings
from app.repositories.station_repository import station_repository
from app.repositories.user_repository import user_repository
from app.repositories.event_repository import event_repository
from app.services.tomtom_service import tomtom_service
from app.services.notification_service import send_status_change_email
from app.database.connection import connect_to_mongo

logger = logging.getLogger(__name__)

# Create a 'write-only' async client to allow Celery to publish events through Redis.
# This client connects to the Redis message queue.
sio_celery = socketio.AsyncServer(
    client_manager=socketio.AsyncRedisManager(settings.redis_url)
)

@celery_app.task(
    name="app.tasks.realtime_tasks.poll_station_availability_new_version",
    queue="realtime_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def poll_station_availability_new_version(self):
    """
    Async polling task για το speed layer: ελέγχει όλους τους σταθμούς, ανιχνεύει αλλαγές status και δημιουργεί event στο collection events.
    """
    try:
        logger.info("[Speed Layer] Starting real-time availability poll (async/repository version)")
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_async_poll_and_log_events())
        return result
    except Exception as e:
        logger.error(f"Error in poll_station_availability task: {str(e)}")
        raise self.retry(exc=e)

async def _async_poll_and_log_events():
    await connect_to_mongo()
    await station_repository.initialize()
    stations = await station_repository.get_all(limit=1000)
    if not stations:
        logger.info("[Speed Layer] No stations found to check for availability.")
        return {"status": "success", "message": "No stations to check."}
    logger.info(f"[Speed Layer] Found {len(stations)} stations to check.")
    updated_count = 0
    event_count = 0
    for station in stations:
        tomtom_id = station.get("tomtom_id")
        if not tomtom_id:
            logger.warning(f"[Speed Layer] Station missing TomTom ID. Skipping: {station}")
            continue
        try:
            # Fetch real-time availability for this station
            # Η μέθοδος get_station_availability υλοποιήθηκε στο tomtom_service.py
            location = station.get("location", {})
            coordinates = location.get("coordinates", [None, None])
            lat = coordinates[1] if len(coordinates) > 1 else None
            lon = coordinates[0] if len(coordinates) > 1 else None
            fresh_data = await tomtom_service.get_station_availability(tomtom_id, lat=lat, lon=lon)
            if not fresh_data:
                logger.warning(f"[Speed Layer] No availability data for station {tomtom_id}. Skipping.")
                continue
            current_status = fresh_data.get("status", "UNKNOWN")
            last_updated = fresh_data.get("last_updated", datetime.utcnow())
            old_status = station.get("status", "UNKNOWN")
            if old_status != current_status:
                # Update station status
                await station_repository.update_station_status(
                    tomtom_id,
                    current_status,
                    {"last_updated": last_updated}
                )
                updated_count += 1
                # Create event in events collection
                await event_repository.create_station_status_change_event(
                    station_id=tomtom_id,
                    old_status=old_status,
                    new_status=current_status,
                    connector_id="" if not None else "",
                    event_data={"source": "speed_layer"},
                    timestamp=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                event_count += 1
                logger.info(f"[Speed Layer] Event created: {tomtom_id} {old_status} → {current_status}")
            else:
                logger.debug(f"[Speed Layer] Station {tomtom_id}: Status unchanged ('{current_status}').")
        except Exception as e:
            logger.error(f"[Speed Layer] Error updating/checking station {tomtom_id}: {str(e)}")
            continue
    logger.info(f"[Speed Layer] Poll finished. Updated: {updated_count}, Events created: {event_count}")
    return {"status": "success", "updated": updated_count, "events": event_count}

@celery_app.task(
    name="app.tasks.realtime_tasks.poll_station_availability_bulk",
    queue="realtime_queue",
    retry_backoff=True,
    retry_jitter=True,
    retry_max_delay=300,
    max_retries=3,
    bind=True
)
def poll_station_availability_bulk(self):
    """
    Speed layer: κάνει 1 bulk call για status και ενημερώνει μόνο όσα άλλαξαν. Κάνει broadcast μέσω WebSocket.
    """
    try:
        logger.info("[Speed Layer] Starting bulk real-time availability poll")
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_async_bulk_poll_and_broadcast())
        return result
    except Exception as e:
        logger.error(f"Error in poll_station_availability_bulk: {str(e)}")
        raise self.retry(exc=e)

async def _async_bulk_poll_and_broadcast():
    await connect_to_mongo()
    await station_repository.initialize()
    
    stations = await station_repository.get_all_stations()
    if not stations:
        logger.info("[Speed Layer] No stations found to check for availability.")
        return {"status": "success", "message": "No stations to check."}
    logger.info(f"[Speed Layer] Found {len(stations)} stations to check.")
    # Παίρνουμε το bulk status (mock ή πραγματικό)
    # Χρησιμοποιούμε το κέντρο της Αθήνας και μεγάλο radius για παράδειγμα
    lat, lon, radius = 37.9838, 23.7275, 50000
    bulk_status = await tomtom_service.get_bulk_status_by_area(lat, lon, radius)

    changed_stations = []
    updated_count = 0
    
    # Use asyncio.gather to process stations concurrently
    tasks = []
    for station in stations:
        tasks.append(process_station_status(station, bulk_status))

    results = await asyncio.gather(*tasks)
    
    for result in results:
        if result:
            changed_stations.append(result['change_info'])
            updated_count += 1

    if changed_stations:
        logger.info(f"[Speed Layer] Broadcasting {len(changed_stations)} status changes via WebSocket")
        await sio_celery.emit('status_update', {"stations": changed_stations})
        
    logger.info(f"[Speed Layer] Bulk poll finished. Updated: {updated_count}, Notifications sent.")
    return {"status": "success", "updated": updated_count, "changed": len(changed_stations)}

async def process_station_status(station: dict, bulk_status: dict):
    """
    Processes a single station's status, updates DB, and sends notifications.
    """
    tomtom_id = station.get("tomtom_id")
    if not tomtom_id:
        return None

    old_status = station.get("status", "UNKNOWN")
    new_status = bulk_status.get(tomtom_id, old_status)

    if old_status != new_status:
        # 1. Update station status in the database
        await station_repository.update_station_status(
            tomtom_id,
            new_status,
            {"last_updated": datetime.utcnow()}
        )

        # 2. Add entry to historical availability
        await station_repository.add_historical_availability(
            tomtom_id,
            new_status,
            datetime.utcnow()
        )

        change_info = {
            "station_id": tomtom_id,
            "old_status": old_status,
            "new_status": new_status
        }
        
        # 3. Find users who have this station as a favorite
        interested_users = await user_repository.find_premium_users_by_favorite_station(tomtom_id)
        
        # 4. Send email notifications to interested users
        if interested_users:
            station_name = station.get("name", "Unknown Station")
            notification_tasks = []
            for user in interested_users:
                notification_tasks.append(
                    send_status_change_email(user, station_name, old_status, new_status)
                )
            await asyncio.gather(*notification_tasks) # Send emails concurrently
            
        return {'change_info': change_info}
        
    return None 