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
    #print(await orm.pool.fetch("SELECT year FROM teams WHERE number=8221 ORDER BY year"))
    #
    # Close the connection.

    #await ftcpenn.FTCPennScraper.scrape_event("http://www.ftcpenn.org/ftc-events/2018-2019-season/hat-tricks-qualifier")
    #await ftcpenn.FTCPennScraper.scrape_event("http://www.ftcpenn.org/ftc-events/2012-2013-season/pennsylvania-ftc-championship-tournament")

    #async def print_region(team):
    #    print(f"{team.number: <5} {team.name: <64} {team.city + ', ' + team.state_prov: <32} {await RegionHelper.get_region(team)}")

    #await asyncio.gather(*[print_region(team) for team in map(Team.from_record, await orm.pool.fetch("SELECT * from teams ORDER BY number"))])

    qs = """SELECT m.*,'' AS ".",red.*,'' AS ".",blue.* FROM matches AS m 
    INNER JOIN match_scores AS red ON (m.key=red.match_key AND red.alliance_color='red') 
    INNER JOIN match_scores AS blue ON (m.key=blue.match_key AND blue.alliance_color='blue');"""
    #print((await orm.pool.fetch(qs))[0])
    pprint.pprint(await orm.join([Match, MatchScore, MatchScore], ['m', 'red', 'blue'], 
                         ["m.key=red.match_key AND red.alliance_color='red'",
                         "m.key=blue.match_key AND blue.alliance_color='blue'"],
                         where="m.comp_level='f' AND m.key=$1", params=('1314cmp0_fm1',)))
    pprint.pprint(await MatchHelper.get_wlt('ftc8221'))
    await orm.close()

asyncio.get_event_loop().run_until_complete(main())
