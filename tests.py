# Copyright (c) 2024 nggit

import asyncio
import os
import unittest

from sqlite3i import (
    Database, DatabaseStatement, AsyncDatabase, AsyncDatabaseStatement
)


class TestSQLite3i(unittest.TestCase):
    def setUp(self):
        print('[', self.id(), ']')

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.db = AsyncDatabase('test.db', loop=self.loop)
        stmt = self.db.prepare(
            'CREATE TABLE IF NOT EXISTS users ('
            '  id INTEGER PRIMARY KEY,'
            '  name TEXT NOT NULL,'
            '  age INTEGER NOT NULL'
            ');'
        )
        self.assertTrue(self.loop.run_until_complete(stmt.execute()))

    def tearDown(self):
        self.loop.run_until_complete(self.db.close())
        self.loop.close()

        os.unlink('test.db')

    def test_insert_update_delete_select(self):
        async def test():
            stmt = self.db.prepare(
                'INSERT INTO users (name, age) VALUES (?, ?)'
            )
            self.assertTrue(await stmt.execute(['Alice', 22]))
            self.assertTrue(await stmt.execute(['Bob', 42]))

            stmt = self.db.prepare('UPDATE users SET age = age + 2')
            self.assertTrue(await stmt.execute())

            stmt = self.db.prepare('DELETE FROM users WHERE id = 1')
            self.assertTrue(await stmt.execute())

            stmt = self.db.prepare('SELECT * FROM users')
            self.assertTrue(await stmt.execute())
            row = await stmt.fetch()

            self.assertEqual(row['name'], 'Bob')
            self.assertEqual(row['age'], 44)
            self.assertEqual(await stmt.fetch(), None)

        self.loop.run_until_complete(test())

    def test_empty_results(self):
        async def test():
            stmt = self.db.prepare('UPDATE users SET age = 33 WHERE id = 3')
            self.assertFalse(await stmt.execute())

            stmt = self.db.prepare('DELETE FROM users WHERE id = 3')
            self.assertFalse(await stmt.execute())

            stmt = self.db.prepare('SELECT * FROM users WHERE id = 3')
            self.assertFalse(await stmt.execute())

        self.loop.run_until_complete(test())

    def test_incorrect_binding(self):
        async def test():
            stmt = self.db.prepare(
                'INSERT INTO users (name, age) VALUES (?, ?)'
            )
            self.assertFalse(await stmt.execute(['Alice']))

        self.loop.run_until_complete(test())

    def test_no_such_table(self):
        async def test():
            stmt = self.db.prepare('SELECT * FROM user')
            self.assertFalse(await stmt.execute())

        self.loop.run_until_complete(test())

    def test_syntax_error(self):
        async def test():
            stmt = self.db.prepare('ELECT * FROM users')
            self.assertFalse(await stmt.execute())

        self.loop.run_until_complete(test())

    def test_execute_after_close(self):
        async def test():
            await self.db.close()
            stmt = self.db.prepare(
                'INSERT INTO users (name, age) VALUES (?, ?)'
            )
            self.assertTrue(await stmt.execute(['Alice', 22]))

        self.loop.run_until_complete(test())

    def test_close(self):
        async def test():
            await self.db.close()
            self.assertEqual(self.db.connection, None)

        self.loop.run_until_complete(test())

    def test_database(self):
        db = Database('test.db')
        db.connect()

        stmt = db.prepare('INSERT INTO users (name, age) VALUES (?, ?)')
        self.assertTrue(stmt.execute(['Alice', 22]))
        self.assertTrue(stmt.execute(['Bob', 42]))

        stmt = db.prepare('UPDATE users SET age = age + 2')
        self.assertTrue(stmt.execute())

        stmt = db.prepare('DELETE FROM users WHERE id = 1')
        self.assertTrue(stmt.execute())

        db.close()

        stmt = db.prepare('SELECT * FROM users')
        self.assertTrue(stmt.execute())
        row = stmt.fetch()

        self.assertEqual(row['name'], 'Bob')
        self.assertEqual(row['age'], 44)
        self.assertEqual(stmt.fetch(), None)

        db.close()

    def test_invalid_instances(self):
        with self.assertRaises(ValueError) as cm:
            _ = DatabaseStatement(None, '')
            self.assertEqual(
                str(cm.exception), 'db must be an instance of Database'
            )

        with self.assertRaises(ValueError) as cm:
            _ = AsyncDatabaseStatement(None, '')
            self.assertEqual(
                str(cm.exception), 'db must be an instance of AsyncDatabase'
            )

    def test_invalid_arguments(self):
        async def test():
            with self.assertRaises(ValueError):
                stmt = self.db.prepare(None)
                await stmt.execute()

            with self.assertRaises(ValueError):
                stmt = self.db.prepare('SELECT * FROM users')
                await stmt.execute(None)

        self.loop.run_until_complete(test())

    def test_context_manager(self):
        with Database('test.db') as db:
            self.assertTrue(isinstance(db, Database))
            self.assertFalse(isinstance(db, AsyncDatabase))
            stmt = db.prepare('SELECT * FROM users')

            with self.assertRaises(TypeError):
                stmt.execute(timeout=None)

        async def test():
            async with AsyncDatabase('test.db') as db:
                self.assertTrue(isinstance(db, AsyncDatabase))
                stmt = db.prepare('SELECT * FROM users')

                with self.assertRaises(TypeError):
                    await stmt.execute(timeout=None)

        self.loop.run_until_complete(test())


if __name__ == '__main__':
    unittest.main()
