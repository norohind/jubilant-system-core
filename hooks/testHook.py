from HookSystem import HookSystem
from Hook import Hook


class testHook(Hook):
    def update(self, operation_id: int) -> None:
        print('update')


def setup(hook_system: HookSystem) -> None:
    hook_system.add_on_insert_hook(testHook())
