from enum import Enum
from loguru import logger
import os
import requests


class BearerManager:
    class Endpoints(Enum):
        RANDOM = '/random_token'

    def __init__(self, demb_capi_auth: str, base_address: str):

        self.base_address = base_address
        self.demb_capi_auth = demb_capi_auth
        self.session = requests.Session()

    def get_random_bearer(self) -> str:
        """Gets bearer token from capi.demb.design (companion-api project)

        :return: bearer token as str
        """

        bearer_request: requests.Response = self._request(self.Endpoints.RANDOM)

        try:
            bearer: str = bearer_request.json()['access_token']

        except Exception as e:
            logger.exception(f'Unable to parse capi.demb.design answer\nrequested: {bearer_request.url!r}\n'
                             f'code: {bearer_request.status_code!r}\nresponse: {bearer_request.content!r}', exc_info=e)
            raise BearerManagerException(e)

        return bearer

    def _request(self, _endpoint: Endpoints) -> requests.Response:
        endpoint = self.base_address + _endpoint.value
        return self.session.get(url=endpoint, headers={'auth': self.demb_capi_auth}, timeout=10)


class BearerManagerException(Exception):
    def __init__(self, parent_exception: Exception):
        self.parent_exception = parent_exception


bearer_manager = BearerManager(os.environ['DEMB_CAPI_AUTH'], 'https://capi.demb.uk')
