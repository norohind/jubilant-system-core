import sqlite3
from SQLRequests import SQLRequests

db = sqlite3.connect('jubilant-system.sqlite')
db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))


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


def delete_squadron(squad_id: int, suppress_deleted=True) -> None:
    """
    A function to make record in squadrons_deleted table

    :param squad_id: squad_id to mark as deleted
    :param suppress_deleted: if IntegrityError exception due to this squad already
    exists in squadrons_deleted table should be suppressed

    :return:
    """

    try:
        with db:
            operation_id = allocate_operation_id(squad_id)
            db.execute(SQLRequests.delete_squadron, {'squad_id': squad_id, 'operation_id': operation_id})

    except sqlite3.IntegrityError as e:
        if not suppress_deleted:
            raise e
