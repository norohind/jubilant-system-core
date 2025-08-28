from . import Queries
import DB
import HookSystem
from loguru import logger

hook_system = HookSystem.HookSystem()


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
            hook_system.notify_deleted(operation_id)

    else:
        # Then we got valid squad_info dict
        news_info = None  # Queries.get_squad_news(squad_id)
        # since Vanguards update NEWS_ENDPOINT always returns 500 b'{"status":500,"message":"Internal Server Error","tag":"bbbdpzgnssvbp"}'

        squad_id_received = squad_info['squad_id']
        if squad_id_received != squad_id:
            # A particular case is 90188 which returns 99719 in response
            # Querying 99719 directly, returns 99719
            logger.warning(f"squad id mismatch: requested {squad_id}, got {squad_id_received}. Treating as deleted: {not suppress_absence}")
            if not suppress_absence:
                operation_id = DB.delete_squadron(squad_id)
                # TODO: Fire notify_deleted, perhaps?

        else:
            operation_id = DB.insert_info_news(news_info, squad_info)
            hook_system.notify_inserted(operation_id)

    return operation_id
