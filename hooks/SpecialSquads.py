import json

from HookSystem import HookSystem
from Hook import Hook
import HookUtils
import sqlite3
from loguru import logger

special_squads_db = sqlite3.connect('file:SPECIAL_SQUADRONS.sqlite?mode=ro&nolock=1', uri=True, check_same_thread=False)
schema = "create table if not exists special_squadrons (id integer primary key, name text);"


def is_special_squadron(squad_id: int) -> bool:
    if bool(special_squads_db.execute('select count(*) from special_squadrons where id = ?;', (squad_id,)).fetchone()[
                0]):
        logger.info(f'Special squadron: {squad_id}')
        return True

    else:
        return False


class DeleteSpecialSquad(Hook):
    def update(self, operation_id: int, last_records) -> None:
        last_record: dict = last_records[0]

        if last_record is None:
            return

        if not is_special_squadron(last_record['squad_id']):
            return

        message = f'Deleted SPECIAL squad `{last_record["name"]}` [last_record["tag"]]\nplatform: {last_record["platform"]}, members: {last_record["member_count"]}, ' \
                  f'created: {last_record["created"]}, owner: `{last_record["owner_name"]}`'
        HookUtils.notify_discord(message)


class UpdateSpecialSquad(Hook):
    def update(self, operation_id: int, last_records: list[dict]) -> None:
        if not is_special_squadron(last_records[0]['squad_id']):
            return

        if len(last_records) == 2:
            last_records[0]['user_tags'] = json.loads(last_records[0]['user_tags'])
            last_records[1]['user_tags'] = json.loads(last_records[1]['user_tags'])
            latest_record = last_records[0]

            message = HookUtils.diff_columns(
                last_records,
                [
                    HookUtils.Column('member_count', 'Members count:'),
                    HookUtils.Column('online_count', 'Online count:'),
                    HookUtils.Column('pending_count', 'Pending count:'),
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
                    HookUtils.generate_message_header(latest_record, 'SPECIAL') + message
                )

        else:
            HookUtils.notify_discord(f'SPECIAL SQUADRON, {operation_id=}, {len(last_records)=}')


def setup(hs: HookSystem):
    # Since main connection is RO, here we create schema in separate RW connection
    db = sqlite3.connect('SPECIAL_SQUADRONS.sqlite')
    db.executescript(schema)
    db.close()

    hs.add_on_delete_hook(DeleteSpecialSquad())
    hs.add_on_insert_hook(UpdateSpecialSquad())
