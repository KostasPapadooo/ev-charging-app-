from app.core.celery_config.celery_app import celery_app
import logging
from datetime import datetime
import asyncio
from app.repositories.station_repository import station_repository
from app.repositories.event_repository import event_repository
from app.services.tomtom_service import tomtom_service
from app.database.connection import connect_to_mongo

logger = logging.getLogger(__name__)

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