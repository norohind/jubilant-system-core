import os
import time
import json
import requests
from .BearerManager import bearer_manager, BearerManagerException
from loguru import logger
from dataclasses import dataclass, field

from . import Exceptions


"""
Functions to perform queries to FDEV
"""


BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'
NEWS_ENDPOINT = 'news/list'


@dataclass
class Proxy:
    url: str | None
    session: requests.sessions.Session = field(init=False)
    last_try: int = 0

    def __post_init__(self):
        self.session = requests.sessions.Session()
        if self.url is not None:
            self.session.proxies.update({'https': self.url})


class ProxiesManager:
    PROXIES_DICT: list[Proxy] = list()
    TIME_BETWEEN_REQUESTS: float = 3.0

    def __init__(self):
        try:
            proxies = json.load(open('proxies.json', 'r'))
            for proxy in proxies:
                self.PROXIES_DICT.append(Proxy(url=proxy['url']))

        except FileNotFoundError:
            self.PROXIES_DICT.append(Proxy(url=None))

        try:
            self.TIME_BETWEEN_REQUESTS = float(os.getenv("JUBILANT_TIME_BETWEEN_REQUESTS"))

        except TypeError:
            pass

    def get_proxy(self, do_sleep=True) -> Proxy:
        selected_proxy = min(self.PROXIES_DICT, key=lambda x: x.last_try)
        if do_sleep:
            time_to_sleep: float = (selected_proxy.last_try + self.TIME_BETWEEN_REQUESTS) - time.time()

            if 0 < time_to_sleep <= self.TIME_BETWEEN_REQUESTS:
                logger.debug(f'Sleeping {time_to_sleep} s')
                time.sleep(time_to_sleep)

        selected_proxy.last_try = time.time()

        return selected_proxy


proxies_manager = ProxiesManager()


def request(url: str, method: str = 'get', **kwargs) -> requests.Response:
    """Makes request through one of proxies in round-robin manner, respects fdev request kd for every proxy

    :param url: url to request
    :param method: method to use in request
    :param kwargs: kwargs
    :return: requests.Response object
    """

    while True:
        proxy = proxies_manager.get_proxy()
        logger.debug(f'Requesting {method.upper()} {url!r}, kwargs: {kwargs}; Using {proxy.url} proxy')

        try:
            proxiedFapiRequest: requests.Response = proxy.session.request(
                method=method,
                url=url,
                headers={'Authorization': f'Bearer {bearer_manager.get_random_bearer()}'},
                **kwargs
            )

            logger.debug(f'Request complete, code {proxiedFapiRequest.status_code!r}, len '
                         f'{len(proxiedFapiRequest.content)}')

        except requests.exceptions.ConnectionError as e:
            logger.error(f'Proxy {proxy.url} is invalid: {str(e.__class__.__name__)}')
            continue

        except BearerManagerException as e:
            logger.opt(exception=True).error(f'Error on getting bearer token')
            continue

        if proxiedFapiRequest.status_code == 418:  # FAPI is on maintenance
            logger.warning(f'{method.upper()} {proxiedFapiRequest.url} returned 418, content dump:\n{proxiedFapiRequest.content!r}')
            raise Exceptions.FAPIDownForMaintenance

        if proxiedFapiRequest.status_code == 504:
            # Rate limited
            logger.info(f'Rate limited to {url!r} via {proxy.url}')
            continue

        elif proxiedFapiRequest.status_code != 200:
            logger.warning(f"Request to {method.upper()} {url!r} with kwargs: {kwargs}, using {proxy.url} "
                           f"proxy ends with {proxiedFapiRequest.status_code} status code, content: "
                           f"{proxiedFapiRequest.content}")

        return proxiedFapiRequest
