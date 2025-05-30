from app.repositories.station_repository import station_repository
from app.repositories.user_repository import user_repository
from app.repositories.event_repository import event_repository
from app.repositories.notification_repository import notification_repository

class Repositories:
    def __init__(self):
        self._stations = None
        self._users = None
        self._events = None
        self._notifications = None
    
    @property
    def stations(self):
        if self._stations is None:
            self._stations = station_repository
        return self._stations
    
    @property
    def users(self):
        if self._users is None:
            self._users = user_repository
        return self._users
    
    @property
    def events(self):
        if self._events is None:
            self._events = event_repository
        return self._events
    
    @property
    def notifications(self):
        if self._notifications is None:
            self._notifications = notification_repository
        return self._notifications

repositories = Repositories() 