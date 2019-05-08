import asyncio
import os
import time

import aiohttp
import uvloop
import csv
import pprint
import re
import datetime
import unicodedata

from bs4 import BeautifulSoup
from loaders.old_champs import OldChamps
from models import Event, EventType, Award, AwardType, PlayoffType, EventParticipant, Match, \
    MatchScore, Ranking
from helpers import ResultsPageHelper, EventHelper, RegionHelper, year_to_season, AwardHelper, \
    MatchDetailsHelper, LocationHelper
from db.orm import orm
import aiotoa
import aiotoa.models

__all__ = ["TOAScraper"]
poprint = lambda o: pprint.pprint(o.__dict__ if hasattr(o, "__dict__") else o)
piprint = lambda i: list(map(poprint, i))
def season_to_year(season):
    season = int(season)
    return (season % 100) - 1 + 2000

class TOAScraper:
    ses: aiotoa.TOASession = None

    @classmethod
    def get_session(cls):
        if not cls.ses:
            with open("toa.key") as f:
                s = f.read().split("\n")
            cls.ses = aiotoa.TOASession(s[0], app_name=s[1])
        return cls.ses
    @classmethod
    async def close(cls):
        await cls.ses.close()

    @classmethod
    def convert_event_type(cls, event_type_key):
        return {
            "LGCMP": EventType.LEAGUE_CMP,
            "LGMEET": EventType.MEET,
            "OFFSSN": EventType.OTHER,
            "QUAL": EventType.QUALIFIER,
            "RCMP": EventType.REGIONAL_CMP,
            "SCRIMMAGE": EventType.SCRIMMAGE,
            "SPRING": EventType.OTHER,
            "SPRQUAL": EventType.SUPER_QUAL,
            "SPRRGNL": EventType.SUPER_REGIONAL,
            "WRLDCMP": EventType.WORLD_CHAMPIONSHIP,
            "OTHER": EventType.OTHER
        }[event_type_key]

    @classmethod
    def load_event(cls, tevent: aiotoa.models.Event):
        event = Event(key=tevent.event_key.lower().replace("-", ""),
                      event_code=tevent.event_key,
                      year=season_to_year(tevent.season_key),
                      name=tevent.event_name,
                      city=tevent.city,
                      state_prov=LocationHelper.unabbrev_state_prov(tevent.country, tevent.state_prov or ""),
                      country=tevent.country,
                      start_date=tevent.start_date,
                      end_date=tevent.end_date,
                      event_type=cls.convert_event_type(tevent.event_type_key),
                      region=RegionHelper.region_abbrev_cache.get(tevent.region_key, tevent.region_key),
                      venue=tevent.venue,
                      website=tevent.website,
                      league_key=tevent.league_key.lower().replace("-", "") if tevent.league_key else None,
                      field_count=tevent.field_count,
                      playoff_type=PlayoffType.STANDARD if tevent.alliance_count == 4 else PlayoffType.BRACKET_8_ALLIANCE,
                      data_sources=["The Orange Alliance"])
        if tevent.division_key is not None:
            if tevent.division_key == 0:
                event.division_keys = [event.key[:-1] + "1", event.key[:-1] + "2"]
            else:
                event.parent_event_key = event.key[:-1] + "0"
            if tevent.division_name:
                event.name += f" - {tevent.division_name} Division"
        return event

    @classmethod
    async def load_matches(cls, event: Event):
        pass

    @classmethod
    async def load(cls, season):
        cls.get_session()
        all_events = await cls.ses.query_events(season_key=season, includeTeamCount=True)
        for e in all_events:
            if e.team_count:
                event = cls.load_event(e)

        # if team_count = 0 then skip

    @classmethod
    async def test(cls):
        cls.get_session()
        e = await cls.ses.event("1718-AK-CMP")
        event = cls.load_event(e)
        piprint(await cls.ses.event_matches(event.event_code))

async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    await RegionHelper.update_region_cache()
    #await TOAScraper.load(1718)
    await TOAScraper.test()
    await TOAScraper.close()
    await orm.close()

if __name__ == "__main__":
    # update events set city='Austin', state_prov='Texas' where key ~ '1617txalaml' or key ~ '1617txalsd' or key ~ '1617txalch';
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

