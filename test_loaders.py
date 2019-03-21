import asyncio
import asyncpg
import datetime
import pprint
import runtime
from models import Team
from helpers import RegionHelper
from db.orm import orm
from data import ftcpenn

async def main():
    await runtime.setup_orm(orm)
    #print(await orm.pool.fetch("SELECT year FROM teams WHERE number=8221 ORDER BY year"))
    #
    # Close the connection.

    #await ftcpenn.FTCPennScraper.scrape_event("http://www.ftcpenn.org/ftc-events/2018-2019-season/hat-tricks-qualifier")
    #await ftcpenn.FTCPennScraper.scrape_event("http://www.ftcpenn.org/ftc-events/2012-2013-season/pennsylvania-ftc-championship-tournament")

    await ftcpenn.FTCPennScraper.get_events(2018)
    await orm.close()

asyncio.get_event_loop().run_until_complete(main())
