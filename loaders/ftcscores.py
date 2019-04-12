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
    MatchDetailsHelper
from db.orm import orm

__all__ = ["FTCScoresScraper"]

def decode_date(d):
    return datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%fZ")

class FTCScoresScraper:
    MIN_TIMEOUT = 1
    timer = 0
    http = None

    @classmethod
    def get_http(cls):
        if not cls.http:
            cls.http = aiohttp.ClientSession(headers={"User-Agent": "FTCData Project FTCScores Scraper"})
        return cls.http

    @classmethod
    async def get(cls, url):
        cls.get_http()
        now = time.time()
        if now - cls.timer < cls.MIN_TIMEOUT:
            await asyncio.sleep(now - cls.timer)
        async with cls.http.get(url) as response:
            return await response.json()

    @classmethod
    def load_matches(cls, data, event_key):
        matches = []
        for m in data["matches"]:
            comp_level, mnum, set_number = ResultsPageHelper.parse_match_code(m['number'])
            match = Match(event_key=event_key, comp_level=comp_level, match_number=mnum, set_number=set_number)
            match.gen_keys()
            red_score, blue_score = m['scores']['red'], m['scores']['blue']
            if red_score > blue_score:
                match.winner = "red"
            elif blue_score > red_score:
                match.winner = "blue"
            else:
                match.winner = "tile"
            red = MatchScore(key=match.red_key, alliance_color="red", event_key=event_key, match_key=match.key,
                             dqed=[], teams=[], surrogates=[], total=red_score)
            blue = MatchScore(key=match.blue_key, alliance_color="blue", event_key=event_key, match_key=match.key,
                             dqed=[], teams=[], surrogates=[], total=blue_score)
            for team in m['teams']['red']:
                red.teams.append(f'ftc{team["number"]}')
                if team['surrogate']:
                    red.surrogates.append(f'ftc{team["number"]}')
            for team in m['teams']['blue']:
                blue.teams.append(f'ftc{team["number"]}')
                if team['surrogate']:
                    blue.surrogates.append(f'ftc{team["number"]}')
            red.auto = m['subscoresRed']['auto']
            red.teleop = m['subscoresRed']['tele']
            red.endgame = m['subscoresRed']['endg']
            red.penalty = m['subscoresRed']['pen']
            blue.auto = m['subscoresBlue']['auto']
            blue.teleop = m['subscoresBlue']['tele']
            blue.endgame = m['subscoresBlue']['endg']
            blue.penalty = m['subscoresBlue']['pen']
            # TODO: load match details (if available)

            matches.append((match, red, blue))
        return matches

    @classmethod
    def load_rankings(cls, data, matches, event_key):
        # since ftcscores has basically everything we need, we just load it right in!
        _, wlt = ResultsPageHelper.highscores_wlt(matches)
        rankings = []
        for r in data['rankings']:
            c = r['current']
            tkey = f"ftc{r['number']}"
            twlt = wlt[tkey]
            ranking = Ranking(event_key=event_key, team_key=tkey,
                              rank=r['rank'], qp_rp=c['qp'], rp_tbp=c['rp'], high_score=c['highest'],
                        wins=twlt[0], losses=twlt[1], ties=twlt[2], dqed=0, played=c['matches'])
            rankings.append(ranking)
        return rankings

    @classmethod
    def get_event_type(cls, data):
        res = {
            "League": EventType.MEET,
            "League Championship": EventType.LEAGUE_CMP,
            "Qualifier": EventType.QUALIFIER,
            "Regional": EventType.REGIONAL_CMP,
            "Super-Regional": EventType.SUPER_REGIONAL,
            "World Championship": EventType.WORLD_CHAMPIONSHIP,
            "Scrimmage": EventType.SCRIMMAGE,
        }[data['type']]

        if "Super" in data['shortName'] and res == EventType.QUALIFIER:
            # ftcscores considers superquals as qualifiers (oops)
            return EventType.SUPER_QUAL
        else:
            return res

    @classmethod
    def load_event_base(cls, data):
        name = data['fullName'] + (" - " + data['subtitle']) if 'subtitle' in data else ''
        short_name = data['shortName']
        country = "USA"
        location = data['location'].split(",")
        if len(location) == 2:
            city, state_prov = location
            venue = None
        else:
            venue, city, state_prov = location
        if ("Super" in name and "Regional" in name) or "World" in name:
            region = None
        elif len(location) == 3:
            region = "Nevada"
        elif "Texas" in state_prov:
            region = "Texas Alamo" # txal is the only region that uses this thing
        elif short_name.startswith("LA"):
            region = "California Los Angeles"
        elif short_name.startswith("NY-HV"):
            region = "New York Hudson Valley"
        else:
            region = state_prov
        if state_prov == "Israel":
            state_prov, country = "", "Israel"
        year = 2000 + (int(data['season']) // 100)
        return Event(
            name=name,
            year=year, city=city, state_prov=state_prov, country=country,
            venue=venue, region=region, playoff_type=PlayoffType.BO3_FINALS,
            start_date=decode_date(data['startDate']),
            end_date=decode_date(data['endDate']),
            event_type=cls.get_event_type(data),
            lat=data['locationCoords']['coordinates'][0],
            lon=data['locationCoords']['coordinates'][1],
            data_source=["FTCScores"]
        )

    @classmethod
    async def load_1617velv(cls):
        # only look at status=completed events
        # we only really care about velocity vortex hmmmm
        finals_data = await cls.get("https://api.ftcscores.com/api/events/1617-south-supers-finals")
        pemberton_data = await cls.get("https://api.ftcscores.com/api/events/1617-south-supers-pemberton")
        kilrain_data = await cls.get("https://api.ftcscores.com/api/events/1617-south-supers-kilrain")
        finals = cls.load_event_base(finals_data)
        pemberton = cls.load_event_base(pemberton_data)
        kilrain = cls.load_event_base(kilrain_data)
        finals.key, pemberton.key, kilrain.key = "1617ssr0", "1617ssr1", "1617ssr2"
        finals.division_keys = [pemberton.key, kilrain.key]
        pemberton.parent_event_key = kilrain.parent_event_key = finals.key
        finals_matches = cls.load_matches(finals_data, finals.key)
        pemberton_matches = cls.load_matches(pemberton_data, pemberton.key)
        kilrain_matches = cls.load_matches(kilrain_data, kilrain.key)

        pemberton_rankings = cls.load_rankings(pemberton_data, pemberton_matches, pemberton.key)
        kilrain_rankings = cls.load_rankings(kilrain_data, kilrain_matches, kilrain.key)

        await EventHelper.insert_event(pemberton, pemberton_matches, pemberton_rankings, None)
        await EventHelper.insert_event(kilrain, kilrain_matches, kilrain_rankings, None)
        await EventHelper.insert_event(finals, finals_matches, None, divisions=[pemberton, kilrain])


async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    #await Event.purge("1516micmp")
    #await FTCDataScraper.load_1516resq()
    #for key in (k['key'] for k in await orm.pool.fetch("SELECT key FROM events WHERE year=2016")):
    #    await Event.purge(key)
    await FTCScoresScraper.load_1617velv()
    await orm.close()

if __name__ == "__main__":
    # update events set city='Austin', state_prov='Texas' where key ~ '1617txalaml' or key ~ '1617txalsd' or key ~ '1617txalch';
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

