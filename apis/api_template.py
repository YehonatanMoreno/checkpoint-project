from abc import ABC

import requests

class APITemplate(ABC):
    BASE_URL = None
    
    @classmethod
    def get(cls, url) -> requests.Response:
        return requests.get(f'{cls.BASE_URL}/{url}')