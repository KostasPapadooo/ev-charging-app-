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

# Configure Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'update-stations-athens-area': {
        'task': 'app.tasks.batch_tasks.batch_update_stations',
        'schedule': crontab(minute='*/30'),  # Κάθε 30 λεπτά
        'args': (ATHENS_CENTER_LAT, ATHENS_CENTER_LON, DEFAULT_UPDATE_RADIUS_METERS),
        'options': {'expires': 60 * 5}, # Το task να λήξει αν δεν ξεκινήσει σε 5 λεπτά
    },
    'update-stations-thessaloniki-area': {
        'task': 'app.tasks.batch_tasks.batch_update_stations',
        'schedule': crontab(minute='5,35'), # π.χ. στο :05 και :35 για να μην συμπίπτει ακριβώς
        'args': (THESSALONIKI_CENTER_LAT, THESSALONIKI_CENTER_LON, DEFAULT_UPDATE_RADIUS_METERS),
        'options': {'expires': 60 * 5},
    },
    'cleanup-historical-data': {
        'task': 'app.tasks.batch_tasks.cleanup_old_historical_data_task',
        'schedule': crontab(hour=3, minute=0),  # Κάθε μέρα στις 3:00 π.μ.
        'args': (30,),  # Διατήρηση δεδομένων για 30 ημέρες (η παράμετρος days_to_keep)
        'options': {'expires': 60 * 60}, # Το task να λήξει αν δεν ξεκινήσει σε 1 ώρα
    },
}

celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE 