import os
import time
import json
import requests
from .BearerManager import bearer_manager, BearerManagerException
from loguru import logger
from . import Exceptions


"""
Functions to perform queries to FDEV
"""


BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'
NEWS_ENDPOINT = 'news/list'

try:
    PROXIES_DICT: list[dict] = json.load(open('proxies.json', 'r'))

except FileNotFoundError:
    PROXIES_DICT: list[dict] = [{'url': None, 'last_try': 0}]


TIME_BETWEEN_REQUESTS: float = 3.0
if os.getenv("JUBILANT_TIME_BETWEEN_REQUESTS") is not None:
    try:
        TIME_BETWEEN_REQUESTS = float(os.getenv("JUBILANT_TIME_BETWEEN_REQUESTS"))

    except TypeError:  # env doesn't contain a float
        pass


def request(url: str, method: str = 'get', **kwargs) -> requests.Response:
    """Makes request through one of proxies in round-robin manner, respects fdev request kd for every proxy

    :param url: url to request
    :param method: method to use in request
    :param kwargs: kwargs
    :return: requests.Response object

    detect the oldest used proxy
    if selected proxy is banned, then switch to next
    detect how many we have to sleep to respect 3 sec timeout for each proxy
    sleep it
    perform request with it
    if request failed -> write last_try for current proxy and try next proxy
    """

    global PROXIES_DICT

    while True:

        selected_proxy = min(PROXIES_DICT, key=lambda x: x['last_try'])
        logger.debug(f'Requesting {method.upper()} {url!r}, kwargs: {kwargs}; Using {selected_proxy["url"]} proxy')

        # let's detect how much we have to wait
        time_to_sleep: float = (selected_proxy['last_try'] + TIME_BETWEEN_REQUESTS) - time.time()

        if 0 < time_to_sleep <= TIME_BETWEEN_REQUESTS:
            logger.debug(f'Sleeping {time_to_sleep} s')
            time.sleep(time_to_sleep)

        proxies: None | dict
        if selected_proxy['url'] is None:
            proxies = None

        else:
            proxies = {'https': selected_proxy['url']}

        try:
            proxiedFapiRequest: requests.Response = requests.request(
                method=method,
                url=url,
                proxies=proxies,
                headers={'Authorization': f'Bearer {bearer_manager.get_random_bearer()}'},
                **kwargs
            )

            logger.debug(f'Request complete, code {proxiedFapiRequest.status_code!r}, len '
                         f'{len(proxiedFapiRequest.content)}')

        except requests.exceptions.ConnectionError as e:
            logger.error(f'Proxy {selected_proxy["url"]} is invalid: {str(e.__class__.__name__)}')
            selected_proxy['last_try'] = time.time()  # Anyway set last try to now
            continue

        except BearerManagerException as e:
            logger.opt(exception=True).error(f'Error on getting bearer token')
            continue

        selected_proxy['last_try'] = time.time()  # Set last try to now

        if proxiedFapiRequest.status_code == 418:  # FAPI is on maintenance
            logger.warning(f'{method.upper()} {proxiedFapiRequest.url} returned 418, content dump:\n{proxiedFapiRequest.content!r}')
            raise Exceptions.FAPIDownForMaintenance

        if proxiedFapiRequest.status_code == 504:
            # Rate limited
            selected_proxy['last_try'] = time.time()  # Anyway set last try to now
            logger.info(f'Rate limited to {url!r} via {selected_proxy["url"]}')
            continue

        elif proxiedFapiRequest.status_code != 200:
            logger.warning(f"Request to {method.upper()} {url!r} with kwargs: {kwargs}, using {selected_proxy['url']} "
                           f"proxy ends with {proxiedFapiRequest.status_code} status code, content: "
                           f"{proxiedFapiRequest.content}")

        return proxiedFapiRequest
