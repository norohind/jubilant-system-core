import os
import functools
import sqlite3

from Hook import Hook
import importlib.machinery
import HookUtils
import copy
from loguru import logger
import threading


def check_int(func: callable) -> callable:
    @functools.wraps(func)
    def decorated(self, operation_id: int | None) -> None:
        if type(operation_id) == int:
            return func(self, operation_id)

    return decorated


def _last_records(operation_id: int, limit: int) -> list[dict]:
    last_exception: Exception | None = None

    for retry in range(0, 10):
        try:
            return Hook.get_db().execute(
                HookUtils.SQL_REQUESTS.GET_HISTORICAL_INFO,
                {'limit': limit, 'operation_id': operation_id}
            ).fetchall()

        except sqlite3.DatabaseError as e:
            if retry != 0:
                logger.opt(exception=True).warning(f'Exception in {threading.current_thread().name}, retry: {retry}')

            last_exception = e
            continue

        except Exception as e:
            logger.opt(exception=True).warning(f'Exception in {threading.current_thread().name}, retry: {retry}')
            last_exception = e
            continue

    with open('retries_list.txt', mode='a') as retries_file:
        retries_file.write(f'{operation_id}:{limit} \n')

    raise last_exception


class HookSystem:
    hooks_inserted: list[Hook] = list()
    hooks_deleted: list[Hook] = list()

    def __init__(self):
        # hooks load
        for file_name in sorted(os.listdir('hooks')):
            if file_name.endswith('.py') and not file_name[0] in ['.', '_']:
                path = os.path.join('hooks', file_name)
                hook_name = file_name[:-3]
                module = importlib.machinery.SourceFileLoader(hook_name, path).load_module()
                setup_func = getattr(module, 'setup', None)
                if setup_func is not None:
                    setup_func(self)

                else:
                    raise AttributeError(f'No setup method in {file_name} hook')

    def add_on_insert_hook(self, hook: Hook) -> None:
        self.hooks_inserted.append(hook)

    def remove_on_insert_hook(self, hook: Hook) -> None:
        self.hooks_inserted.remove(hook)

    def add_on_delete_hook(self, hook: Hook) -> None:
        self.hooks_deleted.append(hook)

    def remove_on_delete_hook(self, hook: Hook) -> None:
        self.hooks_deleted.remove(hook)

    @check_int
    def notify_inserted(self, operation_id: int) -> None:
        self._notify(operation_id, self.hooks_inserted, lambda: _last_records(operation_id, 2))

    @check_int
    def notify_deleted(self, operation_id: int) -> None:
        self._notify(operation_id, self.hooks_deleted, lambda: _last_records(operation_id, 1))

    @staticmethod
    def _notify(operation_id, hooks: list[Hook], get_latest: callable) -> None:
        """
        What here happen?
        `_notify` calls by `notify_deleted` and `notify_inserted` which supplies callable `get_latest` which allows to get
        the latest records for appropriate squadron under `operation_id`.
        We don't want to run logic under `get_latest` in main thread since will slow down performance, instead of it,
        we call it in separate `bootstrap-hook-thread` thread, which calls then `_call_hooks` with resolved latest records,
        and thus we avoid:
        1. Running `get_latest` in main thread
        2. Running same by functionality logic by every hook (it would just generate meaningless cpu load)

        :param operation_id:
        :param hooks:
        :param get_latest:
        :return:
        """

        threading.Thread(
            name=f'bootstrap-hook-thread-{operation_id}',
            target=lambda: HookSystem._call_hooks(operation_id, hooks, get_latest()),
        ).start()

    @staticmethod
    def _call_hooks(operation_id: int, hooks: list[callable], latest_records: list[dict]):
        for hook in hooks:
            threading.Thread(
                name=f'hook-{hook.__class__.__name__}-{operation_id}',
                target=hook.update,
                args=(operation_id, copy.deepcopy(latest_records))
            ).start()
