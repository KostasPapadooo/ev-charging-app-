from app.tasks.batch_tasks import batch_update_stations, cleanup_old_historical_data_task
from app.core.beat_config import ATHENS_CENTER_LAT, ATHENS_CENTER_LON, DEFAULT_UPDATE_RADIUS_METERS

def run_tests():
    print("Sending batch_update_stations task...")
    # Χρησιμοποίησε τις συντεταγμένες και την ακτίνα που έχεις ορίσει
    result_update = batch_update_stations.delay(
        ATHENS_CENTER_LAT,
        ATHENS_CENTER_LON,
        DEFAULT_UPDATE_RADIUS_METERS
    )
    print(f"Task batch_update_stations sent with ID: {result_update.id}")

    print("\nSending cleanup_old_historical_data_task (keeping data for last 1 day for test)...")
    # Για να τεστάρεις το cleanup, βεβαιώσου ότι έχεις δεδομένα παλαιότερα από 1 ημέρα
    # ή ρύθμισε το days_to_keep=0 για να δεις αν διαγράφει παλαιότερα δεδομένα.
    result_cleanup = cleanup_old_historical_data_task.delay(days_to_keep=1) # ή days_to_keep=0
    print(f"Task cleanup_old_historical_data_task sent with ID: {result_cleanup.id}")

if __name__ == '__main__':
    run_tests() 