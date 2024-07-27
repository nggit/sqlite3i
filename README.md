# sqlite3i

[![codecov](https://codecov.io/gh/nggit/sqlite3i/branch/main/graph/badge.svg?token=V6VAU8RNN0)](https://codecov.io/gh/nggit/sqlite3i)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=nggit_sqlite3i&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=nggit_sqlite3i)

An opinionated [sqlite3](https://docs.python.org/3/library/sqlite3.html) wrapper.

The main goal of this package is simply to have `stmt.execute()` return `bool` instead of a cursor object.
So that it can be useful to indicate `True` if the query succeeds, or `False` otherwise.
Empty results on `INSERT`, `UPDATE`, `DELETE`, and `SELECT` are considered as `False`.

It adopts the *prepare - execute* pattern merely for the user experience.

## Synchronous usage
```python
from sqlite3i import Database

db = Database('example.db')


def main():
    try:
        db.connect(timeout=30)

        stmt = db.prepare(
            'CREATE TABLE IF NOT EXISTS users ('
            '  id INTEGER PRIMARY KEY,'
            '  name TEXT NOT NULL,'
            '  age INTEGER NOT NULL'
            ');'
        )
        stmt.execute()  # True

        stmt = db.prepare('SELECT * FROM users')
        stmt.execute()  # False, no rows yet!

        stmt = db.prepare('SELECT * FROM user')
        stmt.execute()  # False, no such table!

        stmt = db.prepare(
            'INSERT INTO users (name, age) VALUES (?, ?)'
        )
        stmt.execute(['Alice'])  # False
        stmt.execute(['Alice', 30])  # True

        stmt = db.prepare('SELECT * FROM users LIMIT 10')
        stmt.execute()  # True
        row = stmt.fetch()

        while row:
            print('*', row['name'], row['age'])
            row = stmt.fetch()
    finally:
        db.close()

if __name__ == '__main__':
    main()
```

## Asynchronous usage
Asyncronous usage is powered by [awaiter](https://pypi.org/project/awaiter/).

The following example uses an asynchronous context manager, although the *try - finally* approach as above can still be used.

```python
import asyncio

from sqlite3i import AsyncDatabase


async def main():
    async with AsyncDatabase('example.db') as db:
        stmt = db.prepare(
            'CREATE TABLE IF NOT EXISTS users ('
            '  id INTEGER PRIMARY KEY,'
            '  name TEXT NOT NULL,'
            '  age INTEGER NOT NULL'
            ');'
        )
        await stmt.execute(timeout=30)

        stmt = db.prepare(
            'INSERT INTO users (name, age) VALUES (?, ?)'
        )
        await stmt.execute(['Alice', 30])

        stmt = db.prepare('SELECT * FROM users LIMIT 10')
        await stmt.execute()
        row = await stmt.fetch()

        while row:
            print('*', row['name'], row['age'])
            row = await stmt.fetch()

if __name__ == '__main__':
    asyncio.run(main())
```

## Install
```
python3 -m pip install --upgrade sqlite3i
```

## License
MIT
