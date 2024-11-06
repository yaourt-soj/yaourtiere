import requests
import json
from config.variables import secrets


class AmplitudeManager:
    def __init__(self):
        self.__headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        self.__data = {
            "api_key": secrets.amplitude_api_key,
            "events": []
        }

    def track(self, event: dict):
        self.__data["events"].append(event)

        response = requests.post('https://api.eu.amplitude.com/2/httpapi',
                                 headers=self.__headers, data=json.dumps(self.__data))
        return response.status_code
