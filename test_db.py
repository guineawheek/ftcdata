import asyncio
import asyncpg
import datetime
import pprint
import runtime
from models import Team, Match, MatchScore
from helpers import RegionHelper, MatchHelper
from db.orm import orm
#from data import ftcpenn

async def main():
    await runtime.setup_orm(orm)
    meet_keys = ['1415paphlm1', '1415paphlm2', '1415paphlm3']
    qs = "SELECT DISTINCT a.team_key FROM event_participants AS a INNER JOIN event_participants" \
         "AS b ON (a.event_key=ANY($1) AND a.team_key=b.team_key AND b.team_key"
    pprint.pprint({r['team_key'] for r in await orm.pool.fetch(qs, meet_keys)})
    await orm.close()

asyncio.get_event_loop().run_until_complete(main())
