import hashlib

def generate_area_id(lat: float, lon: float, radius: int) -> str:
    """
    Δημιουργεί ένα μοναδικό identifier για μια γεωγραφική περιοχή
    με βάση τις συντεταγμένες και την ακτίνα.
    Χρησιμοποιούμε grid-based approach για να ομαδοποιούμε κοντινές τοποθεσίες.
    """
    # Στρογγυλοποίηση σε 2 δεκαδικά για grid περίπου 1.1km x 1.1km
    grid_lat = round(lat, 2)
    grid_lon = round(lon, 2)
    # Δημιουργία hash από τις στρογγυλοποιημένες συντεταγμένες και την ακτίνα
    area_string = f"{grid_lat}:{grid_lon}:{radius}"
    return hashlib.md5(area_string.encode()).hexdigest() 