import asyncio
import aiohttp
import asyncpg
import uvloop
import datetime
import pprint
import gzip
import pickle
from models import Event, Award, Match, MatchScore
from helpers import LocationHelper, ChampSplitHelper
from data import ftcpenn
from db.orm import orm


async def add_event(url, event_code):
    awards, rankings, match_details = ftcpenn.scrape_event(url)
    print(awards, rankings, match_details)
    #async with orm.pool.acquire() as conn:
    #    async with conn.transaction():
            


async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()


    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())
