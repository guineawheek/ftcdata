import asyncio
import aiohttp
import asyncpg
import uvloop
import datetime
import pprint
import gzip
import pickle
from models import Team, TeamMeta
from helpers import LocationHelper, ChampSplitHelper, RegionHelper, NominatimHelper
from db.orm import orm

record_counter = 0

async def add_team(data):
    global record_counter
    UPSERT = True
    number = data["number"]
    rookie_year = data["rookie_year"]
    async with orm.pool.acquire() as conn:
        async with conn.transaction():
            for s in data["seasons"]:
                url = s['website']
                if url and (not url.startswith("http://") or not url.startswith("https://")):
                    url = "http://" + url
                team = Team(
                        key=f"ftc{number}",
                        number=number,
                        year=s['year'],
                        rookie_year=rookie_year,
                        name=s['name'],
                        org=s['org'],
                        motto=s['motto'],
                        home_cmp='',
                        city=s['city'],
                        state_prov=s['state_prov'],
                        country=s['country'],
                        postalcode=s['postal_code'],
                        normalized_location='',
                        website=url,
                        lat=s["location"][0],
                        lon=s["location"][1]
                )
                team.state_prov = LocationHelper.unabbrev_state_prov_team(team)
                team.region = await RegionHelper.get_region(team)
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
    record_counter += 1
    print(f"loading {record_counter} teams...", end="\r")


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
    await NominatimHelper.http.close()
    print("done.\nUpdating team_meta...")
    await TeamMeta.update()

    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())
