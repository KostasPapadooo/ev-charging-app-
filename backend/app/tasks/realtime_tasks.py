import logging
from datetime import datetime
from typing import List, Dict, Any

from app.core.celery_config import celery_app
from app.services.tomtom_service import tomtom_service
from app.repositories import station_repo, init_repositories
from app.models.station import Station, ConnectorInfo

logger = logging.getLogger(__name__)

@celery_app.task(
    name='app.tasks.realtime_tasks.poll_station_availability',
    retry_backoff=True,
    retry_jitter=True,
    autoretry_for=(Exception,), # Retry for any exception
    max_retries=3,
    retry_backoff_max=300, # Max 5 minutes backoff
    acks_late=True, # Ensure task is acknowledged after completion
    reject_on_worker_lost=True
)
def poll_station_availability() -> Dict[str, Any]:
    """
    Polls TomTom API for real-time availability of stations and updates the database.
    """
    try:
        init_repositories() # Ensure repositories are initialized in the Celery worker process
        logger.info("Starting real-time availability poll for stations.")

        if not station_repo:
            logger.error("StationRepository not initialized in poll_station_availability task.")
            return {"status": "error", "message": "StationRepository not initialized."}

        # 1. Get all TomTom IDs from our current_stations collection
        station_tomtom_ids: List[str] = station_repo.get_all_station_tomtom_ids_sync()
        if not station_tomtom_ids:
            logger.info("No stations found in the database to poll for availability.")
            return {"status": "success", "message": "No stations to poll.", "updated_count": 0, "checked_count": 0}

        logger.info(f"Found {len(station_tomtom_ids)} stations to check for availability.")

        # 2. Fetch real-time availability from TomTom
        # This method handles chunking internally
        availability_data_list: List[Dict[str, Any]] = tomtom_service.get_stations_availability_sync(station_tomtom_ids)

        if not availability_data_list:
            logger.info("No availability data returned from TomTom service.")
            return {"status": "success", "message": "No availability data from TomTom.", "updated_count": 0, "checked_count": len(station_tomtom_ids)}

        updated_stations_count = 0
        processed_station_ids = set()

        for avail_data in availability_data_list:
            tomtom_id = avail_data.get("tomtom_id")
            new_overall_status = avail_data.get("overall_status")
            api_connector_statuses = avail_data.get("connectors", []) # List of {"id": "conn_id", "status": "STATUS"}

            if not tomtom_id or not new_overall_status:
                logger.warning(f"Skipping availability data due to missing tomtom_id or overall_status: {avail_data}")
                continue
            
            processed_station_ids.add(tomtom_id)

            # 3. Get the existing station model from our database
            existing_station: Station = station_repo.get_station_by_tomtom_id_sync(tomtom_id)
            if not existing_station:
                logger.warning(f"Station {tomtom_id} found in availability API response but not in our DB. Skipping update.")
                continue

            # 4. Compare and update
            station_changed = False
            
            # Update overall status and count changes
            if existing_station.status != new_overall_status:
                logger.info(f"Station {tomtom_id}: Overall status changed from '{existing_station.status}' to '{new_overall_status}'.")
                existing_station.status = new_overall_status
                existing_station.availability_status_changes_count += 1
                station_changed = True

            # Update connector statuses
            if existing_station.connectors and api_connector_statuses:
                for db_connector in existing_station.connectors:
                    if not db_connector.id: # Should have an ID from initial import
                        logger.warning(f"DB Connector for station {tomtom_id} is missing an ID. Cannot match with API availability.")
                        continue
                    
                    # Find matching connector from API response
                    api_connector_update = next((cs for cs in api_connector_statuses if cs.get("id") == db_connector.id), None)
                    
                    if api_connector_update:
                        new_connector_status = api_connector_update.get("status")
                        if new_connector_status and db_connector.status != new_connector_status:
                            logger.info(f"Station {tomtom_id}, Connector {db_connector.id}: Status changed from '{db_connector.status}' to '{new_connector_status}'.")
                            db_connector.status = new_connector_status
                            station_changed = True
            
            if station_changed:
                existing_station.last_updated = datetime.utcnow()
                try:
                    update_success = station_repo.update_station_sync(existing_station)
                    if update_success:
                        logger.info(f"Successfully updated station {tomtom_id} with new availability.")
                        updated_stations_count += 1
                    else:
                        logger.warning(f"Update reported no modification for station {tomtom_id}, though changes were detected.")
                except Exception as e_update:
                    logger.error(f"Error updating station {tomtom_id} in DB: {e_update}", exc_info=True)
            else:
                # Even if no data change, we might want to update 'last_updated' to show it was checked.
                # However, for this layer, we only update if there's an actual data change.
                # If you want to update last_updated always, uncomment below and adjust update_station_sync logic.
                # existing_station.last_updated = datetime.utcnow()
                # station_repo.update_station_sync(existing_station) # This would require update_station_sync to handle no-change updates gracefully
                logger.debug(f"No availability changes detected for station {tomtom_id}.")


        logger.info(f"Real-time availability poll finished. Checked: {len(processed_station_ids)} stations. Updated: {updated_stations_count} stations.")
        return {
            "status": "success",
            "checked_count": len(processed_station_ids),
            "updated_count": updated_stations_count,
            "total_in_db_initially": len(station_tomtom_ids)
        }

    except Exception as e:
        logger.error(f"Error in poll_station_availability task: {str(e)}", exc_info=True)
        # The autoretry_for will handle this if it's a retryable exception
        raise # Re-raise to allow Celery to handle retries 