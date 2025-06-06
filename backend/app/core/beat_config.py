from celery.schedules import crontab
from datetime import timedelta
from app.core.config import settings

# Default locations to monitor (major Greek cities)
MONITORED_LOCATIONS = [
    {
        "name": "Athens",
        "latitude": 37.9838,
        "longitude": 23.7275,
        "radius": 50000  # 50km radius
    },
    {
        "name": "Thessaloniki",
        "latitude": 40.6401,
        "longitude": 22.9444,
        "radius": 30000  # 30km radius
    },
    {
        "name": "Patras",
        "latitude": 38.2466,
        "longitude": 21.7345,
        "radius": 20000  # 20km radius
    }
]

# Celery Beat Schedule Configuration
beat_schedule = {
    # Batch update stations for each monitored location
    **{
        f'update-stations-{location["name"].lower()}': {
            'task': 'app.tasks.batch_tasks.batch_update_stations',
            'schedule': timedelta(hours=5),  # Run every 5 hours
            'args': (
                location["latitude"],
                location["longitude"],
                location["radius"],
                location["name"]
            )
        } for location in MONITORED_LOCATIONS
    },
    
    # Cleanup old historical data (runs daily at 03:00)
    'cleanup-historical-data': {
        'task': 'app.tasks.batch_tasks.cleanup_old_historical_data',
        'schedule': crontab(hour=3, minute=0),
        'args': (30,)  # Keep 30 days of historical data
    },
    
    # Cache cleanup (runs every 6 hours)
    'cleanup-cache': {
        'task': 'app.tasks.cache_cleanup.cleanup_old_cache',
        'schedule': timedelta(hours=6),
        'args': ()
    },

    "speed_layer_bulk": {
        "task": "app.tasks.realtime_tasks.poll_station_availability_bulk",
        "schedule": timedelta(minutes=5),
    },
}

# Task Routing
task_routes = {
    'app.tasks.batch_tasks.*': {'queue': 'batch_queue'},
    'app.tasks.realtime_tasks.*': {'queue': 'realtime_queue'},
    'app.tasks.cache_cleanup.*': {'queue': 'maintenance_queue'}
} 