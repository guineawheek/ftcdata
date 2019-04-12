import asyncio
import asyncpg
import datetime
import pprint
import runtime
from helpers.league_helper import LeagueHelper
from models import Team, Match, MatchScore, Event
from helpers import RegionHelper, MatchHelper
from db.orm import orm
#from data import ftcpenn

async def main():
    await runtime.setup_orm(orm)
    event = await Event.select_one(props={"key": "1415paphlm4"})
    pprint.pprint(sorted(await LeagueHelper.calc_rankings_before(event), reverse=True))
    await orm.close()

asyncio.get_event_loop().run_until_complete(main())
