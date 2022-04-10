import sqlite3
from SQLRequests import SQLRequests

db = sqlite3.connect('jubilant-system.sqlite')
db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
db.executescript(SQLRequests.schema)


class settings:
    @staticmethod
    def set(key: str, value: str | int):
        if isinstance(value, int):
            with db:
                db.execute(
                    SQLRequests.settings_set_int,
                    {'int_value': value, 'key': key}
                )

        else:
            with db:
                db.execute(
                    SQLRequests.settings_set_str,
                    {'str_value': value, 'key': key}
                )


def enable_triggers() -> None:
    settings.set('disable_triggers', 0)


def disable_triggers() -> None:
    settings.set('disable_triggers', 1)


enable_triggers()


def allocate_operation_id(squad_id: int) -> int:
    return db.execute(SQLRequests.create_operation_id, {'squad_id': squad_id}).fetchone()['operation_id']


def insert_info_news(news_dict: dict | None, info_dict: dict) -> int:
    """
    Saved both news and info endpoint's data

    :param news_dict:
    :param info_dict:
    :return:
    """

    with db:
        operation_id = allocate_operation_id(info_dict['squad_id'])
        info_dict['operation_id'] = operation_id

        db.execute(SQLRequests.insert_info, info_dict)

        if news_dict is not None:
            news_dict['type_of_news'] = 'public_statements'
            news_dict['operation_id'] = operation_id
            db.execute(SQLRequests.insert_news, news_dict)

    return operation_id


def delete_squadron(squad_id: int, suppress_deleted=True) -> int | None:
    """
    A function to make record in squadrons_deleted table and returns operation_id with squad_deletion
    or None if squad wasn't deleted

    :param squad_id: squad_id to mark as deleted
    :param suppress_deleted: if IntegrityError exception due to this squad already
    exists in squadrons_deleted table should be suppressed

    :return: operation_id or None
    """

    try:
        with db:
            operation_id = allocate_operation_id(squad_id)
            db.execute(SQLRequests.delete_squadron, {'squad_id': squad_id, 'operation_id': operation_id})

        return operation_id

    except sqlite3.IntegrityError as e:
        if not suppress_deleted:
            raise e


def build_squadrons_current_data() -> None:
    db.executescript(SQLRequests.build_squadrons_current_data)


def last_known_squadron() -> int:
    if (res := db.execute(SQLRequests.last_known_squadron).fetchone()) is None:
        return 0

    else:
        return res['squad_id']


def get_backupdate_squad_ids(limit: int) -> list[int]:
    return [squad_row['squad_id'] for squad_row in db.execute(SQLRequests.select_new_squadrons_backupdate, {'limit': limit}).fetchall()]


def get_squads_for_update(limit: int) -> list[int]:
    return [squad_row['squad_id'] for squad_row in db.execute(SQLRequests.get_squads_for_update, {'limit': limit}).fetchall()]


def ensure_squadrons_current_data_exists() -> None:
    if db.execute(SQLRequests.ensure_squadrons_current_state_exists).fetchone()['count'] == 0:
        build_squadrons_current_data()
