import requests
from .BearerManager import bearer_manager
from loguru import logger
from . import Exceptions


"""
Functions to perform queries to FDEV
"""


BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'
NEWS_ENDPOINT = 'news/list'


def request(url: str, method: str = 'get', **kwargs) -> requests.Response:
    _request: requests.Response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': f'Bearer {bearer_manager.get_random_bearer()}'},
        **kwargs
    )

    if _request.status_code == 418:  # FAPI is on maintenance
        logger.warning(f'{method.upper()} {_request.url} returned 418, content dump:\n{_request.content}')

        raise Exceptions.FAPIDownForMaintenance

    return _request
