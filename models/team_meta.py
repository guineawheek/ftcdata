from db.orm import orm
from db.types import *
class TeamMeta(orm.Model):
    __tablename__ = "team_meta"
    __primary_key__ = ("key",)
    key: text
    number: integer
    rookie_year: integer
    last_competed: integer
    region: text

    @classmethod
    async def update(cls):
        async with orm.pool.acquire() as conn:
            async with conn.transaction():
                #select key, number, rookie_year, max(year) as last_competed from teams group by key,number,rookie_year;
                return await cls.fetch(f"INSERT INTO {cls.__schemaname__}.{cls.__tablename__} "
                                        "(key, number, rookie_year, last_competed) "
                                        "SELECT key, number, rookie_year, max(year) as last_competed "
                                        "FROM public.teams GROUP BY key, number, rookie_year "
                                        "ON CONFLICT (key) DO UPDATE SET last_competed=EXCLUDED.last_competed")
