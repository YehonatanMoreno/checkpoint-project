import logging
import requests
from abc import ABC

class APITemplate(ABC):
    BASE_URL = None
    
    @classmethod
    def get(cls, url) -> requests.Response:
        try:
            res = requests.get(f'{cls.BASE_URL}/{url}')
            APITemplate.handle_response_errors(res)
            return res
        except Exception as e:
            logging.error(f"Error while requesting {cls.BASE_URL}: {e}")
            raise e

    @staticmethod    
    def handle_response_errors(res: requests.Response) -> None:
        if 400 <= res.status_code < 600:
            if res.status_code == 404:
                raise Exception("Error code 404 - not found")
            raise Exception(f"Error code {res.status_code}: {res.text}")
