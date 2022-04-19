import sqlite3
from abc import ABC, abstractmethod
import os


class Hook(ABC):  # See at Hook class as to observer in observer pattern
    """
    In order to implement hook, subclass this class and pass instance to HookSystem.add_hook
    """

    @abstractmethod
    def update(self, operation_id: int, latest: list[dict]) -> None:
        """

        :param operation_id: operation id
        :param latest: latest information about squad in operation_id, in case of delete, it 1 last record,
        in case of update it 2 records for update and 1 record for discovery
        :return:
        """

        raise NotImplemented

    @staticmethod
    def get_db() -> sqlite3.Connection:
        """
        One connection per request is only one method to avoid sqlite3.DatabaseError: database disk image is malformed.
        Connections in sqlite are extremely cheap (0.22151980000001004 secs for 1000 just connections and
        0.24141229999999325 secs for 1000 connections for this getter, thanks timeit)
        and don't require to be closed, especially in RO mode. So, why not?

        :return:
        """

        db = sqlite3.connect(f'file:{os.environ["DB_PATH"]}?mode=ro&nolock=1', check_same_thread=False, uri=True)
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        return db
