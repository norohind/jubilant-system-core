import json

from HookSystem import HookSystem
from Hook import Hook
import HookUtils


class DeleteRuSquad(Hook):
    """
    Send alert to discord if was removed russian squad
    """

    def update(self, operation_id: int) -> None:
        last_record: dict = self.get_db().execute(
            HookUtils.SQL_REQUESTS.GET_HISTORICAL_INFO,
            {
                'limit': 1,
                'operation_id': operation_id
            }
        ).fetchone()

        if last_record is not None:  # i.e. we have a record in db for this squad
            if 32 in json.loads(last_record['user_tags']):  # 32 - russian tag
                message = f'Deleted RU squad `{last_record["name"]}` [{last_record["tag"]}]\nplatform: {last_record["platform"]}, members: {last_record["member_count"]}, ' \
                      f'created: {last_record["created"]}, owner: `{last_record["owner_name"]}`'
                HookUtils.notify_discord(message)


class UpdateRuSquad(Hook):
    """
    Send alert to discord if something important was changed for ru squad
    """

    def update(self, operation_id: int) -> None:
        last_records = self.get_db().execute(
            HookUtils.SQL_REQUESTS.GET_HISTORICAL_INFO,
            {
                'limit': 2,
                'operation_id': operation_id
            }
        ).fetchall()

        if len(last_records) == 1:
            # Squad just discovered
            record = last_records[0]
            if '32' in record['user_tags']:
                message = f"""
name: `{record['name']}` [{record['tag']}]
members: {record['member_count']}
created: {record['created']}
platform: {record['platform']}
owner: `{record['owner_name']}`
tags:\n{HookUtils.humanify_resolved_user_tags(HookUtils.resolve_user_tags(record['user_tags']))}
motd: `{record['motd']}`
motd author: `{record['author']}`
"""
                HookUtils.notify_discord(message)
        elif len(last_records) == 2:
            # Squad updated
            last_records[0]['user_tags'] = json.loads(last_records[0]['user_tags'])
            last_records[1]['user_tags'] = json.loads(last_records[1]['user_tags'])

            latest_record = last_records[0]

            if 32 not in [*last_records[0]['user_tags'], *last_records[1]['user_tags']]:
                return

            message = HookUtils.diff_columns(
                last_records,
                [
                    HookUtils.Column('member_count', 'Members count:'),
                    HookUtils.Column('accepting_new_members', 'Accepting new members:'),
                    HookUtils.Column('user_tags', '', is_user_tags=True),
                    HookUtils.Column('owner_name', 'Ownership:', is_screen_values=True),
                    HookUtils.Column('owner_id', 'Owner FID:'),
                    HookUtils.Column('motd', 'Motd:', is_screen_values=True),
                    HookUtils.Column('author', 'Motd author:', is_screen_values=True),
                    HookUtils.Column('faction_name', 'Faction:')
                ]
            )

            if message != '':
                HookUtils.notify_discord(
                    HookUtils.generate_message_header(latest_record, 'RU') + message
                )

        else:
            HookUtils.notify_discord(f'{operation_id=}, {len(last_records)=}')


def setup(hs: HookSystem):
    hs.add_on_delete_hook(DeleteRuSquad())
    hs.add_on_insert_hook(UpdateRuSquad())
