from abc import ABC, abstractmethod


class Hook(ABC):  # See at Hook class as to observer in observer pattern
    """
    In order to implement hook, subclass this class and pass instance to HookSystem.add_hook
    """

    @abstractmethod
    def update(self, operation_id: int) -> None:
        raise NotImplemented
