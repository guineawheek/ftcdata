import json

import asyncpg

from .types import Column

"""
A very, very barebones asyncpg-backed ORM.

Shouldn't be vulnerable to SQL injection provided that 
__schemaname__, __tablename__, __primary_key__, and _columns are not set to 
arbitrary user input. 

That would be really, really bad.

One can use the defualt orm instance or instantiate your own for other dbs.

"""


class ORM:
    def __init__(self):
        class Model:
            __schemaname__ = "public"
            __tablename__ = None
            __primary_key__ = None
            __addn_sql__ = None

            # kwargs are just a way to put in fields
            def __init__(self, conn=None, **kwargs):
                self.conn = conn
                self.__dict__.update({k:None for k in self._columns.keys()})
                self.__dict__.update(kwargs)

            def __repr__(self):
                return self.__class__.__name__ + "(" + ", ".join(f"{key}={val!r}" for key, val in \
                        {key: getattr(self, key) for key in self._columns.keys() if getattr(self, key) is not None}.items()) + ")"

            @classmethod
            async def create_all_tables(cls):
                async with self.pool.acquire() as conn:
                    for scls in Model.__subclasses__():
                        columns = {}
                        for field_name, field_type in scls.__annotations__.items():
                            if isinstance(field_type, Column):
                                columns[field_name] = field_type.sql
                        scls._columns = columns
                        scls._orm = self

                        async with conn.transaction():
                            db_columns = await conn.fetch("SELECT column_name from information_schema.columns "
                                                          "WHERE table_schema = $1 AND table_name = $2",
                                                          scls.__schemaname__, scls.__tablename__)

                            if db_columns:
                                db_column_names = set(map(lambda r: r["column_name"], db_columns))
                                column_names = set(columns.keys())
                                if column_names - db_column_names:
                                    raise TypeError(f"columns {column_names - db_column_names} are missing from the database!")
                            else:

                                query_params = ", ".join(map(" ".join, zip(columns.keys(), columns.values())))
                                if scls.__addn_sql__:
                                    query_params += ", " + scls.__addn_sql__
                                if scls.__primary_key__:
                                    query_params += f", PRIMARY KEY({', '.join(k for k in scls.__primary_key__)})"
                                # "but making sql like this is bad, you say." Yes. Yes it is. It is assumed, however, that this code
                                # is never fed user inputs, in which case you probably just want a real ORM anyway.
                                query_str = f"CREATE TABLE IF NOT EXISTS {scls.__schemaname__}.{scls.__tablename__}({query_params})"
                                await conn.fetch(query_str)

            @classmethod
            def from_record(cls, record: asyncpg.Record):
                if record is None:
                    return None
                ret = cls()
                for field in cls._columns.keys():
                    setattr(ret, field, record[field])
                return ret

            @classmethod
            async def fetch(cls, *args, conn=None):
                if conn is None:
                    async with cls._orm.pool.acquire() as conn:
                        async with conn.transaction():
                            return [cls.from_record(r) for r in await conn.fetch(*args)]
                else:
                    async with conn.transaction():
                        return [cls.from_record(r) for r in await conn.fetch(*args)]

            @classmethod
            async def fetchrow(cls, *args, conn=None):
                if conn is None:
                    async with cls._orm.pool.acquire() as conn:
                        async with conn.transaction():
                            return cls.from_record(await conn.fetchrow(*args))
                else:
                    async with conn.transaction():
                        return cls.from_record(await conn.fetchrow(*args))

            async def insert(self, conn=None, upsert=""):
                fields = self._columns.keys()
                qs = f"INSERT INTO {self.__schemaname__}.{self.__tablename__}({','.join(fields)}) VALUES(" + ",".join(
                    f"${i}" for i in range(1, len(fields) + 1)) + ")" + (" ON CONFLICT DO " + upsert if upsert else "")
                args = [qs] + [getattr(self, f) for f in fields]
                await self.fetch(*args, conn=conn)

            @classmethod
            async def select(cls, conn=None, **properties):
                if properties is None:
                    return await cls.fetch(f"SELECT * FROM {cls.__schemaname__}.{cls.__tablename__}")
                else:
                    fields = properties.keys()
                    qs = f"SELECT * FROM {cls.__schemaname__}.{cls.__tablename__} WHERE " + " AND ".join(
                        f"${f}=${i}" for i, f in enumerate(fields, 1))
                    return await cls.fetch(*([qs] + list(properties.values())), conn=conn)

            @classmethod
            async def select_one(cls, conn=None, **properties):
                fields = properties.keys()
                qs = f"SELECT * FROM {cls.__schemaname__}.{cls.__tablename__} WHERE " + " AND ".join(f"{f}=${i}" for i, f in enumerate(fields, 1))
                return await cls.fetchrow(*([qs] + list(properties.values())), conn=conn)

            async def update(self, keys=None, conn=None, properties=None):
                pkeys = self.__primary_key__ or tuple()
                if keys is None:
                    fields = [k for k in self._columns.keys() if k not in pkeys]
                else:
                    fields = [k for k in self._columns.keys() if k in keys and k not in pkeys]
                if properties is None:
                    if not pkeys:
                        raise ValueError("properties must be passed to update() if there is no primary key!")
                    else:
                        properties = {k: getattr(self, k) for k in self.__primary_key__}
                qs = f"UPDATE {self.__schemaname__}.{self.__tablename__} SET ({','.join(fields)}) = (" + ",".join(
                    f"${i}" for i in range(1, len(fields) + 1)) + ") " \
                         f"WHERE " + " AND ".join(f"{f} = ${i}" for i, f in enumerate(properties.keys(), len(fields) + 1))
                # print(qs)

                return await self.fetchrow(*([qs] + [getattr(self, f) for f in fields] + list(properties.values())), conn=conn)

            async def delete(self, conn=None, **properties):
                pkeys = self.__primary_key__ or tuple()
                if properties is None:
                    if not pkeys:
                        raise ValueError("properties must be passed to delete() if there is no primary key!")
                    else:
                        properties = {k: getattr(self, k) for k in self.__primary_key__}
                qs = f"DELETE FROM {self.__schemaname__}.{self.__tablename__} WHERE " + " AND ".join(
                    f"{f}=${i}" for i, f in enumerate(properties.keys(), 1))
                return await self.fetch(*([qs] + list(properties.values())), conn=conn)

            @classmethod
            async def delete_all(cls, conn=None, **properties):
                if not properties:
                    raise ValueError("delete_all() requires at least one keyword argument!")
                qs = f"DELETE FROM {cls.__schemaname__}.{cls.__tablename__} WHERE " + " AND ".join(
                    f"{f}=${i}" for i, f in enumerate(properties.keys(), 1))
                return await cls.fetch(*([qs] + list(properties.values())), conn=conn)

            def primary_key(self):
                if not self.__primary_key__:
                    return None
                return tuple(getattr(self, k) for k in self.__primary_key__)

            async def upsert(self, conn=None):
                """this performs an upsert by doing a select then an insert/update, this can be subject to race conditions
                and should be avoided if possible."""
                if not self.__primary_key__:
                    # ig i could implement a checker?
                    raise TypeError("upsert() requires a primary key on the table")
                if await self.select_one(**{k: getattr(self, k) for k in self.__primary_key__}, conn=conn):
                    await self.update(conn=conn)
                else:
                    await self.insert(conn=conn)

        self.Model = Model
        self.pool: asyncpg.pool.Pool

    async def connect(self, **kwargs):
        async def connection_initer(conn):
            await conn.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )

        kwargs["init"] = connection_initer
        self.pool = await asyncpg.create_pool(**kwargs)

    async def close(self):
        await self.pool.close()


orm = ORM()
