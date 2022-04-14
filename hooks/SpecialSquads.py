import json

from HookSystem import HookSystem
from Hook import Hook
import HookUtils
import sqlite3

special_squads_db = sqlite3.connect('file:SPECIAL_SQUADRONS.sqlite?mode=ro', uri=True)
schema = "create table if not exists special_squadrons (id integer primary key, name text);"
special_squads_db.executescript(schema)


def is_special_squadron(squad_id: int) -> bool:
    return bool(special_squads_db.execute('select count(*) from special_squadrons where id = ?;', (squad_id,)).fetchone()[0])


class DeleteSpecialSquad(Hook):
    def update(self, operation_id: int) -> None:
        last_record: dict = self.get_db().execute(
            HookUtils.SQL_REQUESTS.GET_HISTORICAL_INFO,
            {
                'limit': 1,
                'operation_id': operation_id
            }
        ).fetchone()

        if last_record is None:
            return

        if not is_special_squadron(last_record['squad_id']):
            return

        message = f'Deleted SPECIAL squad `{last_record["name"]}` [last_record["tag"]]\nplatform: {last_record["platform"]}, members: {last_record["member_count"]}, ' \
                      f'created: {last_record["created"]}, owner: `{last_record["owner_name"]}`'
        HookUtils.notify_discord(message)


class UpdateSpecialSquad(Hook):
    def update(self, operation_id: int) -> None:
        last_records: list[dict] = self.get_db().execute(
            HookUtils.SQL_REQUESTS.GET_HISTORICAL_INFO,
            {
                'limit': 2,
                'operation_id': operation_id
            }
        ).fetchall()

        if len(last_records) == 2 and is_special_squadron(last_records[0]['squad_id']):
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
    hs.add_on_delete_hook(DeleteSpecialSquad())
    hs.add_on_insert_hook(UpdateSpecialSquad())