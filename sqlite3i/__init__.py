# Copyright (c) 2024 nggit

__version__ = '0.0.2'
__all__ = ('Database', 'AsyncDatabase')

import logging  # noqa: E402
import sqlite3  # noqa: E402

logger = logging.getLogger('sqlite3i')

try:
    from awaiter import ThreadExecutor
except ImportError:  # pragma: no cover
    logger.error(
        'awaiter package is needed by AsyncDatabase but not installed'
    )


class DatabaseStatement:
    def __init__(self, db, query):
        if not isinstance(db, Database):
            raise ValueError('db must be an instance of Database')

        self.db = db
        self.query = query
        self.cursor = None
        self.rows = []

    def fetch(self):
        try:
            return self.rows.pop(0)
        except IndexError:
            if self.cursor:
                return self.cursor.fetchone()

    def execute(self, parameters=(), timeout=30):
        try:
            conn = Database.connect(self.db, timeout=timeout)
            conn.row_factory = sqlite3.Row
            self.cursor = conn.execute(self.query, parameters)

            if self.cursor.description:
                # SELECT
                row = self.cursor.fetchone()

                if row:
                    self.rows.append(row)
                    return True

                return False

            # INSERT, UPDATE, etc.
            conn.commit()

            # Read-only attribute that provides the number of modified rows
            # for INSERT, UPDATE, DELETE, and REPLACE statements;
            # is -1 for other statements, including CTE queries.
            return self.cursor.rowcount != 0

        except sqlite3.DatabaseError as exc:
            logger.error('execute: %s', str(exc))
            # something is wrong (it could be the connection),
            # avoid reusing the connection to ensure robustness
            Database.close(self.db)

            return False


class AsyncDatabaseStatement(DatabaseStatement):
    def __init__(self, db, query):
        if not isinstance(db, AsyncDatabase):
            raise ValueError('db must be an instance of AsyncDatabase')

        super().__init__(db, query)

    def fetch(self):
        return self.db.executor.submit(super().fetch)

    def execute(self, *args, **kwargs):
        self.db.connect(timeout=kwargs.get('timeout', 30))
        return self.db.executor.submit(super().execute, *args, **kwargs)


class Database:
    def __init__(self, database):
        self.database = database
        self.connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def connect(self, **kwargs):
        if self.connection is None:
            logger.info('(re)connecting to database %s', self.database)
            self.connection = sqlite3.connect(self.database, **kwargs)

        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def prepare(self, query):
        return DatabaseStatement(self, query)


class AsyncDatabase(Database):
    def __init__(self, database, **kwargs):
        self.executor = ThreadExecutor(**kwargs)
        super().__init__(database)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def connect(self, **kwargs):
        if not self.executor.is_alive():
            try:
                self.executor.start()
            except RuntimeError as exc:
                logger.error('connect: %s. recreating executor...', str(exc))
                self.executor = ThreadExecutor()
                self.executor.start()

        return self.executor.submit(super().connect, **kwargs)

    def close(self):
        if self.executor.is_alive():
            self.executor.submit(super().close)

        return self.executor.shutdown()

    def prepare(self, query):
        return AsyncDatabaseStatement(self, query)
