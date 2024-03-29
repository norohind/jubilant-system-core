from loguru import logger
import threading
import time

import FAPI
import signal
import DB
import sys
import inspect
import logging

logger.remove()
logger.add(sys.stderr, diagnose=False, colorize=False)  # Please set debug level by env variable LOGURU_LEVEL

shutting_down: bool = False
can_be_shutdown: bool = False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# logging.basicConfig(handlers=[InterceptHandler()], level=0)


def shutdown_callback(sig: int, frame) -> None:
    logger.info(f'Planning shutdown by {sig} signal')
    try:
        frame_info = inspect.getframeinfo(frame)
        func = frame_info.function
        code_line = frame_info.code_context[0]
        logger.info(f'Currently at {func}:{frame_info.lineno}: {code_line!r}')
        running_threads = ', '.join((thread.name for thread in threading.enumerate()))
        logger.info(f'Running threads: {running_threads}')

    except Exception as e:
        logger.info(f"Can't detect where we are because {e}")

    global shutting_down
    shutting_down = True

    if can_be_shutdown:
        logger.info('Can be shutdown')
        exit(0)


def threads_dump(sig: int, frame) -> None:
    running_threads = ', '.join((thread.name for thread in threading.enumerate()))
    logger.info(f'Running threads: {running_threads}')


def discover(back_count: int = 0):
    """Discover new squads
    :param back_count: int how many squads back we should check, it is helpful to recheck newly created squads
    :return:
    """

    id_to_try = DB.last_known_squadron()
    tries: int = 0
    failed: list = list()
    TRIES_LIMIT_RETROSPECTIVELY: int = 5000
    TRIES_LIMIT_ON_THE_TIME: int = 5

    def smart_tries_limit(_squad_id: int) -> int:

        if _squad_id < 65000:
            return TRIES_LIMIT_RETROSPECTIVELY

        else:
            return TRIES_LIMIT_ON_THE_TIME

    """
    tries_limit, probably, should be something more smart because on retrospectively scan we can
    have large spaces of dead squadrons but when we are discovering on real time, large value of tries_limit
    will just waste our time and, probable, confuses FDEV 
    *Outdated but it still can be more smart*
    """

    if back_count != 0:
        logger.debug(f'back_count = {back_count}')

        squad_id: int
        for squad_id in DB.get_backupdate_squad_ids(back_count):
            logger.debug(f'Back updating {squad_id}')
            FAPI.update_squad(squad_id)

    while True:

        if shutting_down:
            return

        id_to_try = id_to_try + 1
        # logger.debug(f'Starting discover loop iteration, tries: {tries} of {tries_limit}, id to try {id_to_try}, '
        #             f'failed list: {failed}')

        if tries == smart_tries_limit(id_to_try):
            break

        squad_operation_id = FAPI.update_squad(id_to_try, suppress_absence=True)

        if squad_operation_id is not None:  # success
            logger.debug(f'Success discover for {id_to_try} ID')
            tries = 0  # reset tries counter

            for failed_squad in failed:  # since we found an exists squad, then all previous failed wasn't exists
                DB.delete_squadron(failed_squad)

            failed = list()

        else:  # fail, should be only False
            logger.debug(f'Fail on discovery for {id_to_try} ID')
            failed.append(id_to_try)
            tries = tries + 1


def update(squad_id: int = None, amount_to_update: int = 1, suppress_absence=True):
    """

    :param suppress_absence: if we're manually updating a squadron which we know for sure are deleted
    :param squad_id: update specified squad, updates only that squad
    :param amount_to_update: update specified amount, ignores when squad_id specified
    :return:
    """

    if isinstance(squad_id, int):
        logger.debug(f'Going to update one specified squadron: {squad_id} ID')
        FAPI.update_squad(squad_id, suppress_absence=suppress_absence)
        # suppress_absence is required because if we're manually updating squad with some high id it may just don't exist yet
        return

    logger.debug(f'Going to update {amount_to_update} squadrons')

    squads_id_to_update: list[int] = DB.get_squads_for_update(amount_to_update)

    for id_to_update in squads_id_to_update:  # if db is empty, then loop will not happen

        if shutting_down:
            return

        logger.info(f'Updating {id_to_update} ID')
        FAPI.update_squad(id_to_update)


def main():
    DB.ensure_squadrons_current_data_exists()
    global can_be_shutdown
    signal.signal(signal.SIGTERM, shutdown_callback)
    signal.signal(signal.SIGINT, shutdown_callback)
    try:
        signal.signal(signal.SIGUSR1, threads_dump)

    except AttributeError:
        pass

    def help_cli() -> str:
        return """Possible arguments:
    main.py discover
    main.py update
    main.py update amount <amount: int>
    main.py update id <id: int>
    main.py force-update id <id: int>
    main.py daemon
    main.py hooks notify <inserted;deleted> <operation_id: int>"""

    logger.debug(f'argv: {sys.argv}')

    if len(sys.argv) == 1:
        print(help_cli())
        exit(1)

    elif len(sys.argv) == 2:
        if sys.argv[1] == 'discover':
            # main.py discover
            logger.info(f'Entering discover mode')
            discover()
            exit(0)

        elif sys.argv[1] == 'update':
            # main.py update
            logger.info(f'Entering common update mode')
            update()
            exit(0)

        elif sys.argv[1] == 'daemon':
            # main.py daemon
            logger.info('Entering daemon mode')
            while True:
                can_be_shutdown = False

                update(amount_to_update=500)
                if shutting_down:
                    exit(0)

                logger.info('Updated, sleeping')
                can_be_shutdown = True
                time.sleep(30 * 60)
                can_be_shutdown = False
                logger.info('Discovering')

                discover(back_count=20)
                if shutting_down:
                    exit(0)

                logger.info('Discovered, sleeping')
                can_be_shutdown = True
                time.sleep(30 * 60)

        else:
            print(help_cli())
            exit(1)

    elif len(sys.argv) == 4:
        if sys.argv[1] in ('update', 'force-update'):
            if sys.argv[2] == 'amount' and sys.argv[1] == 'update':
                # main.py update amount <amount: int>

                try:
                    amount: int = int(sys.argv[3])

                except ValueError:
                    amount = 0
                    print('Amount must be integer')
                    exit(1)

                logger.info(f'Entering update amount mode, amount: {amount}')
                update(amount_to_update=amount)
                exit(0)

            elif sys.argv[2] == 'id':
                # main.py update id <id: int>
                # main.py force-update id <id: int>
                if sys.argv[1] == 'force-update':
                    suppress_absence = False

                else:
                    suppress_absence = True

                try:
                    id_for_update: int = int(sys.argv[3])

                except ValueError:
                    id_for_update = 0
                    print('ID must be integer')
                    exit(1)

                logger.info(f'Entering update specified squad: {id_for_update} ID')
                update(squad_id=id_for_update, suppress_absence=suppress_absence)
                exit(0)

            else:
                logger.info(f'Unknown argument {sys.argv[2]}')

    elif len(sys.argv) == 5:
        # main.py hooks notify <inserted;deleted> <operation_id: int>
        if sys.argv[1] == 'hooks' and sys.argv[2] == 'notify' and sys.argv[3] in ('inserted', 'deleted'):
            try:
                operation_id = int(sys.argv[4])

            except ValueError:
                operation_id = 0
                print('operation_id must be integer')
                exit(1)

            logger.info(f'Notifying {sys.argv[3]} hooks with {operation_id=}')

            if sys.argv[3] == 'inserted':
                FAPI.hook_system.notify_inserted(operation_id)

            else:  # deleted
                FAPI.hook_system.notify_deleted(operation_id)

            exit(0)
    else:
        print(help_cli())
        exit(1)


if __name__ == '__main__':
    main()
