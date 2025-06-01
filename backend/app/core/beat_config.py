from celery.schedules import crontab
from app.core.config import settings

# Define the beat schedule as a dictionary
# This will be loaded into celery_app.conf.beat_schedule later
beat_schedule = {
    'batch-update-athens-stations': {
        'task': 'app.tasks.batch_tasks.batch_update_stations',
        'schedule': crontab(minute=f'*/{settings.BATCH_UPDATE_INTERVAL_MINUTES}'),
        'args': (
            settings.ATHENS_CENTER_LAT,
            settings.ATHENS_CENTER_LON,
            settings.ATHENS_RADIUS_METERS,
            settings.ATHENS_CITY_NAME
        ),
        'options': {'queue': 'batch_queue'}
    },
    'update-stations-thessaloniki-area': {
        'task': 'app.tasks.batch_tasks.batch_update_stations',
        'schedule': crontab(minute='5,35'),
        'args': (
            settings.THESSALONIKI_CENTER_LAT,
            settings.THESSALONIKI_CENTER_LON,
            settings.THESSALONIKI_RADIUS_METERS,
            settings.THESSALONIKI_CITY_NAME
        ),
        'options': {'queue': 'batch_queue'}
    },
    'poll-station-availability-realtime': {
        'task': 'app.tasks.realtime_tasks.poll_station_availability_new_version',
        'schedule': settings.DEFAULT_SPEED_LAYER_POLLING_INTERVAL_SECONDS,
        'args': (),
        'options': {'queue': 'realtime_queue'}
    },
    'cleanup-old-historical-data': {
        'task': 'app.tasks.batch_tasks.cleanup_old_historical_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (settings.HISTORICAL_DATA_RETENTION_DAYS,),
        'options': {'queue': 'batch_queue'}
    }
} 