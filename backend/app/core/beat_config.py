from celery import Celery
from celery.schedules import crontab
from app.core.celery_config import celery_app

# Παράδειγμα για το κέντρο της Αθήνας και μια ακτίνα κάλυψης
ATHENS_CENTER_LAT = 37.9838
ATHENS_CENTER_LON = 23.7275
DEFAULT_UPDATE_RADIUS_METERS = 50000  # 50 χιλιόμετρα, μπορείς να το προσαρμόσεις

# Παράδειγμα για το κέντρο της Θεσσαλονίκης
THESSALONIKI_CENTER_LAT = 40.6401
THESSALONIKI_CENTER_LON = 22.9444

# Default coordinates for Athens and radius for batch updates
DEFAULT_BATCH_UPDATE_INTERVAL_MINUTES = 30 # For Athens
DEFAULT_HISTORICAL_CLEANUP_CRON_HOUR = 2 # At 2 AM
DEFAULT_HISTORICAL_CLEANUP_CRON_MINUTE = 0
DEFAULT_HISTORICAL_DAYS_TO_KEEP = 30

# New: Speed Layer Polling Interval
DEFAULT_SPEED_LAYER_POLLING_INTERVAL_SECONDS = 60 # Poll every 60 seconds

# Configure Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'update-stations-thessaloniki-area': {
        'task': 'app.tasks.batch_tasks.batch_update_stations',
        'schedule': crontab(minute='5,35'), # π.χ. στο :05 και :35 για να μην συμπίπτει ακριβώς
        'args': (THESSALONIKI_CENTER_LAT, THESSALONIKI_CENTER_LON, DEFAULT_UPDATE_RADIUS_METERS),
        'options': {'expires': 60 * 5},
    },
    'batch-update-athens-stations': {
        'task': 'app.tasks.batch_tasks.batch_update_stations',
        'schedule': crontab(minute=f'*/{DEFAULT_BATCH_UPDATE_INTERVAL_MINUTES}'), # Every X minutes
        'args': (ATHENS_CENTER_LAT, ATHENS_CENTER_LON, DEFAULT_UPDATE_RADIUS_METERS),
        'options': {'queue': 'batch_queue'} # Optional: route to a specific queue
    },
    'cleanup-old-historical-data': {
        'task': 'app.tasks.batch_tasks.cleanup_old_historical_data_task',
        'schedule': crontab(hour=DEFAULT_HISTORICAL_CLEANUP_CRON_HOUR, minute=DEFAULT_HISTORICAL_CLEANUP_CRON_MINUTE), # Daily at 2:00 AM
        'args': (DEFAULT_HISTORICAL_DAYS_TO_KEEP,), # Example: Keep data for 30 days
        'options': {'queue': 'batch_queue'}
    },
    # New schedule for real-time availability polling
    'poll-station-availability-realtime': {
        'task': 'app.tasks.realtime_tasks.poll_station_availability',
        'schedule': DEFAULT_SPEED_LAYER_POLLING_INTERVAL_SECONDS, # Run every X seconds
        # No args needed for this task as it fetches all stations from DB
        'options': {'queue': 'realtime_queue'} # Optional: route to a specific queue for speed layer tasks
    },
}

celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE 