from datetime import datetime, timedelta

class Cache:
        def __init__(self):
            self.cache = {}
            self.ttl = 60 * 5  # Cache entries expire after 5 minutes
            self.timestamps = {}
    
        def get(self, key):
            if key in self.cache:
                if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.timestamps[key]
            return self.cache.get(key)
    
        def set(self, key, value, ttl=None):
            if ttl is not None:
                self.ttl = ttl
            self.cache[key] = value
            self.timestamps[key] = datetime.now()