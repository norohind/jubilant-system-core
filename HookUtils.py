import dataclasses
from collections import defaultdict
from loguru import logger
import requests
import os
import json

with open('available.json', 'r', encoding='utf-8') as available_file:
    TAG_COLLECTIONS: dict = json.load(available_file)['SquadronTagData']['SquadronTagCollections']

del available_file


def notify_discord(message: str) -> None:
    """Just sends message to discord, without rate limits respect"""
    logger.debug('Sending discord message')

    if len(message) >= 2000:  # discord limitation
        logger.warning(f'Refuse to send len={len(message)}, content dump:\n{message}')
        message = 'Len > 2000, check logs'

    hookURL: str = os.environ['DISCORD_NOTIFICATIONS_HOOK']
    content: bytes = f'content={requests.utils.quote(message)}'.encode('utf-8')

    discord_request: requests.Response = requests.post(
        url=hookURL,
        data=content,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        proxies={"https": "http://localhost:1080"}
    )

    try:
        discord_request.raise_for_status()

    except Exception as e:
        logger.exception(f'Fail on sending message to discord ({"/".join(hookURL.split("/")[-2:])})'
                         f'\n{discord_request.content}', exc_info=e)
        return

    logger.debug('Sending successful')
    return


class SQL_REQUESTS:
    GET_HISTORICAL_INFO = """
select *
from squadrons_historical_data
    inner join operations_info on squadrons_historical_data.operation_id = operations_info.operation_id
    left join squadrons_news_historical snh on operations_info.operation_id = snh.operation_id
where
      squad_id = (select squad_id from operations_info where operation_id = :operation_id) and
      operations_info.operation_id <= :operation_id
order by operations_info.operation_id desc
limit :limit;
    """


def resolve_user_tag(single_user_tag: int) -> [str, str]:
    """
    Resolves one tag to category and tag itself

    :param single_user_tag:
    :return:
    """
    for tag_collection in TAG_COLLECTIONS:
        for tag in tag_collection['SquadronTags']:
            if tag['ServerUniqueId'] == single_user_tag:
                return tag_collection['localisedCollectionName'], tag['LocalisedString']


def resolve_user_tags(user_tags: list[int]) -> dict[str, list[str]]:
    """Function to resolve user_tags list of ints to dict with tag collections as keys and list of tags as value

    :param user_tags: list of ints of tags to resolve
    :return: dict of tags
    """

    _resolved_tags: dict[str, list[str]] = dict()

    for user_tag in user_tags:
        collection_name, tag_name = resolve_user_tag(user_tag)
        if collection_name in _resolved_tags:  # if key in dict
            _resolved_tags[collection_name].append(tag_name)

        else:
            _resolved_tags.update({collection_name: [tag_name]})

    return _resolved_tags


def humanify_resolved_user_tags(user_tags: dict[str, list[str]], do_tabulate=True) -> str:
    """Function to make result of resolve_user_tags more human-readable

    :param do_tabulate: if we should insert tabulation or you already did it in source data, default to True
    :param user_tags: result of resolve_user_tags function
    :return: string with human-friendly tags list
    """

    result_str: str = str()
    if do_tabulate:
        tab = '    '

    else:
        tab = str()

    for tag_collection_name in user_tags:
        result_str += f"{tag_collection_name}:\n"

        for tag in user_tags[tag_collection_name]:
            result_str += f"{tab}{tag}\n"

    return result_str


def tags_diff2str(new_tags_ids: list, old_tags_ids: list) -> str:
    """Compares two list of tags, new and old, and returns it in diff like str

    :param new_tags_ids: list ids of new tags
    :param old_tags_ids: list ids of old tags
    :return: diff as str
    """

    resolved_tags: dict[str, list[str]] = defaultdict(list)

    removed_tags_ids: list = list(set(old_tags_ids) - set(new_tags_ids))
    added_tags_ids: list = list(set(new_tags_ids) - set(old_tags_ids))

    tags_union_ids: list = list(set(new_tags_ids).union(set(old_tags_ids)))

    for tag_id in tags_union_ids:
        collection_name, tag_name = resolve_user_tag(tag_id)

        if tag_id in removed_tags_ids:
            resolved_tags[collection_name].append(f'-   {tag_name}')

        elif tag_id in added_tags_ids:
            resolved_tags[collection_name].append(f'+   {tag_name}')

        else:  # tag_id not in added_tags_ids and not in removed_tags_ids - nothing changed
            resolved_tags[collection_name].append(f'    {tag_name}')

    return humanify_resolved_user_tags(resolved_tags, do_tabulate=False)


@dataclasses.dataclass
class Column:
    """ For diff_columns"""
    name: str
    label: str
    is_screen_values: bool = False
    is_user_tags: bool = False
    screening_value_start: str = dataclasses.field(init=False)
    screening_value_end: str = dataclasses.field(init=False)

    def __post_init__(self):
        if self.is_screen_values and not self.is_user_tags:
            self.screening_value_start = self.screening_value_end = '`'

        elif self.is_user_tags:
            self.is_screen_values = True
            self.screening_value_start = '```diff\n'
            self.screening_value_end = f'```\n'

        else:
            self.screening_value_start = self.screening_value_end = ''

    def screen(self, value: str) -> str:
        return f'{self.screening_value_start}{value}{self.screening_value_end}'


def diff_columns(info: list[dict], columns_to_diff: list[Column]) -> str:
    """
    Takes list of two history records about squad and returns diff in str for specified column

    :param info: must be two list of two records
    :param columns_to_diff:  list of columns to diff
    :return:
    """

    msg = ''
    new_record = info[0]
    old_record = info[1]
    for column in columns_to_diff:
        new_column = new_record[column.name]
        old_column = old_record[column.name]

        if new_column != old_column:
            if column.is_user_tags:
                msg += column.screen(tags_diff2str(new_column, old_column))

            else:
                msg += f'{column.label} {column.screen(old_column)} -> {column.screen(new_column)}\n'

    return msg


def generate_message_header(record: dict, squadron_type: str) -> str:
    return f"""
State changed for {squadron_type} squad `{record['name']}` [{record['tag']}]
platform: {record['platform']}
members: {record['member_count']}
created: {record['created']}
owner: `{record['owner_name']}`
"""
