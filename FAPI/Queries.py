from .Mappings import perform_info_mapping, perform_news_mapping
from .Exceptions import *
from .Requester import *
from loguru import logger
from . import Converters
import json


def get_squad_news(squad_id) -> dict | None:
    """
    Returns news of squadron with specified id or None if squadron doesn't exists or there is no news

    :param squad_id:
    :return:
    """

    news_request: requests.Response = request(BASE_URL + NEWS_ENDPOINT, params={'squadronId': squad_id})
    if news_request.status_code != 200:  # must not happen
        logger.warning(f'Got not 200 status code on requesting news, content: {news_request.content}, '
                       f'code: {news_request.status_code}')

    squad_news: dict = news_request.json()['squadron']

    if isinstance(squad_news, list):  # check squadron 2517 for example 0_0
        # squadron have no public statements
        return None

    elif 'id' not in squad_news.keys():  # squadron doesn't FDEV
        return None

    else:
        if 'public_statements' in squad_news.keys() and len(squad_news['public_statements']) > 0:
            return perform_news_mapping(squad_news['public_statements'][0])


def get_squad_info(squad_id: int) -> dict | None:
    """Returns information about squadron with specified id or None if squadrons doesn't exists on FDEV side

    :param squad_id: id of squad to update/insert
    :return: dict with state of squadron or None if squad not found
    """

    """
    Request squad's info
    
    if squad exists FDEV
        return squadron state
    
    if squad doesn't exists FDEV        
       return None
    """

    squad_request: requests.Response = request(BASE_URL + INFO_ENDPOINT, params={'squadronId': squad_id})

    if squad_request.status_code == 200:  # squad exists FDEV
        squad_request_json: dict = squad_request.json()['squadron']
        squad_request_json['ownerName'] = Converters.dehexify(squad_request_json['ownerName'])  # normalize value
        squad_request_json['userTags'] = json.dumps(squad_request_json['userTags'])
        squad_request_json = perform_info_mapping(squad_request_json)

        return squad_request_json

    elif squad_request.status_code == 404:  # squad doesn't exists FDEV
        return None

    else:  # any other codes (except 418, that one handles in authed_request), never should happen
        logger.warning(f'Unknown squad info status_code: {squad_request.status_code}, content: {squad_request.content}')
        raise FAPIUnknownStatusCode(f'Status code: {squad_request.status_code}, content: {squad_request.content}')