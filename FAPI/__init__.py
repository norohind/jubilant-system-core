from . import Queries
import DB


def update_squad(squad_id: int, suppress_absence=False) -> None | int:
    """
    Updates specified squad and returns operation_id or None if squad not found
    :param squad_id:
    :param suppress_absence:
    :return:
    """
    squad_info = Queries.get_squad_info(squad_id)
    operation_id = None
    if squad_info is None:
        # Squad not found FDEV
        if not suppress_absence:
            operation_id = DB.delete_squadron(squad_id)

    else:
        # Then we got valid squad_info dict
        news_info = Queries.get_squad_news(squad_id)
        operation_id = DB.insert_info_news(news_info, squad_info)

    return operation_id
