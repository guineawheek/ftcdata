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
    async with orm.pool.acquire() as conn:
        async with conn.transaction():
            awards, rankings, match_details = ftcpenn.scrape_event(url)
            team.state_prov = LocationHelper.unabbreviated_state_prov(team)
            cmps = ChampSplitHelper.get_champ(team)
            if cmps is not None:
                if team.year > 2016:
                    team.home_cmp = cmps[2017]
                elif team.year == 2016:
                    team.home_cmp = cmps[2016]
            if UPSERT:
                await team.upsert(conn=conn)
            else:
                await team.insert(conn=conn)


async def main():
    DATA_URL = "https://ocf.berkeley.edu/~liuderek/ftc_teams.pickle.gz"

    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    print("Downloading " + DATA_URL)
    async with aiohttp.ClientSession() as session:
        async with session.get(DATA_URL) as response:
            data = pickle.loads(gzip.decompress(await response.read()))
    await asyncio.gather(*[add_team(d) for d in data.values()])
    print("done.\nUpdating team_meta...")
    await TeamMeta.update()

    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())
