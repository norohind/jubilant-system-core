import os
import functools
import threading
from Hook import Hook
import importlib.machinery


def check_int(func: callable) -> callable:
    @functools.wraps(func)
    def decorated(self, operation_id: int | None) -> None:
        if type(operation_id) == int:
            return func(self, operation_id)

    return decorated


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
    def notify_inserted(self, operation_id: int | None) -> None:
        self._notify(operation_id, self.hooks_inserted)

    @check_int
    def notify_deleted(self, operation_id: int) -> None:
        self._notify(operation_id, self.hooks_deleted)

    @staticmethod
    def _notify(operation_id, hooks: list[Hook]) -> None:
        for hook in hooks:
            threading.Thread(target=hook.update, args=(operation_id,)).start()
