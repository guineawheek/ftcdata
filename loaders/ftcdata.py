import asyncio
import os

import uvloop
import csv
import pprint
import re
import datetime
import unicodedata

from bs4 import BeautifulSoup
from loaders.old_champs import OldChamps
from models import Event, EventType, Award, AwardType, PlayoffType, EventParticipant
from helpers import ResultsPageHelper, EventHelper, RegionHelper, year_to_season, AwardHelper, \
    MatchDetailsHelper
from db.orm import orm

__all__ = ["FTCDataScraper"]

class FTCDataScraper:
    EVENT_TYPE_MAP = {
        "Meet": EventType.MEET,
        "Super-Qualifier": EventType.SUPER_QUAL,
        "Qualifying Tournament": EventType.QUALIFIER,
        "Qualifier": EventType.QUALIFIER,
        "Super Regional Championship": EventType.SUPER_REGIONAL,
        "League Championship": EventType.LEAGUE_CMP,
        "Championship Tournament": EventType.REGIONAL_CMP,
        "Championship": EventType.REGIONAL_CMP,
        "World Championship": EventType.WORLD_CHAMPIONSHIP
    }

    @classmethod
    async def load_resq_finals(cls, finals):
        with open("data/old_champs/2015-2016/finals.html") as f:
            matches = ResultsPageHelper.load_matches(BeautifulSoup(f.read(), 'lxml').find("table"), "1516cmp0")
            for a, b, c in matches:
                await a.upsert()
                await b.upsert()
                await c.upsert()
            finals.data_sources = ["FTCData Original Research"]
            await finals.upsert()
            await AwardHelper.generate_winners_finalists(finals)


    @classmethod
    def resq_region(cls, name, state, ecode, region_code):
        if state == "California":
            if "Qualifying Tournament" in name:
                return "California NorCal", "canc"
            else:
                return "California Los Angeles", "cala"
        elif state == "Massachusettes":
            # typo in data
            return "Massachusetts", "ma"
        elif state == "New York":
            if "Hudson Valley" in name:
                return "New York Hudson Valley", "nyhv"
            else:
                return "New York Excelsior", "nyex"
        elif state.startswith("Texas"):
            state = "Texas"
            if ecode in {"a2", "ac", "au", "ki", "cmpal"}:
                return "Texas Alamo", "txal"
            elif ecode in {"cmplld", "cmplwh", "cmpse", "hf"}:
                return "Texas Southeast", "txse"
            else: #ecode in {"cmplep", "cmplpps"}:
                return "Texas Panhandle", "txph"
        elif state == "Michigan":
            return "Michigan Highschool", "mihs"
        else:
            return state, region_code

    @classmethod
    async def load_1516resq(cls):
        with open("data/ftc-data/events/1516resq/1516resq-event-list.csv") as f:
            csv_reader = csv.reader(f.read().split("\n"))
        finals = None
        for row in csv_reader:
            if not row:
                continue
            sdate = list(map(int, row[0].split("/")))
            date = datetime.datetime(year=sdate[2], month=sdate[0], day=sdate[1])
            name, state, fevent_type, divno, region_code, ecode, divid, ftcdata_code = [a.strip() for a in row[1:9]]
            divno = int(divno)
            if region_code in ("pa", "esr"):
                # ftcpenn loads this better than ftcdata ever did (oops!)
                continue
            event_type = cls.EVENT_TYPE_MAP[fevent_type]
            event = None
            rcode = "ERROR"
            region = "ERROR"
            country = "USA"
            # append "Division" to the end of names
            if divid != 'x' and not name.endswith("Division"):
                name += " Division"
            if event_type == EventType.WORLD_CHAMPIONSHIP:
                franklin, edison, finals = OldChamps.mk_champs(2015, "2016-04-27", "2016-04-30")
                if ecode == 'ed':
                    event = edison
                elif ecode == 'fr':
                    event = franklin
                await cls.load_resq_finals(finals)
            elif event_type == EventType.SUPER_REGIONAL:
                rcode = region_code
            else:
                region, rcode = cls.resq_region(name, state, ecode, region_code)
                if state == "Canada":
                    state, country = "Alberta", "Canada"

            if ecode.startswith("cmp") and len(ecode) > 3:
                ecode = ecode[3:] + "cmp"
            if event_type == EventType.REGIONAL_CMP:
                ecode = "cmp"
            if event is None:
                event = Event(key=f"1516{rcode}{ecode}",
                              year=2015, name=name, state_prov=state, country=country,
                              start_date=date, end_date=date, event_type=event_type,
                              playoff_type=PlayoffType.STANDARD)
                if event_type != EventType.SUPER_REGIONAL:
                    event.region = region
                if divid != 'x':
                    event.key += str(divno)
                event.event_code = ftcdata_code
            with open(f"data/ftc-data/events/1516resq/{region_code.lower()}/"
                      f"1516resq-{ftcdata_code}-MatchResultsDetails.html") as f:
                matches = ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml'), event.key)

            with open(f"data/ftc-data/events/1516resq/{region_code.lower()}/"
                      f"1516resq-{ftcdata_code}-Rankings.html") as f:
                rankings = ResultsPageHelper.load_rankings(BeautifulSoup(f.read(), 'lxml'), matches)

            await EventHelper.insert_event(event, matches, rankings, None, tolerate_missing_finals=True, data_source="cheer4ftc ftc-data repository")
            print("loaded " + event.key)

    @classmethod
    async def load_1617velv(cls):
        with open("data/ftc-data/events/1617velv/1617velv-event-list.csv") as f:
            csv_reader = csv.reader(f.read().split("\n"))
        for row in csv_reader:
            if not row:
                continue
            sdate = list(map(int, row[0].split("/")))
            date = datetime.datetime(year=sdate[2], month=sdate[0], day=sdate[1])
            name, state, fevent_type, _, region_code, ecode, divid, ftcdata_code, state_abbr, data_quality = [a.strip() for a in row[1:]]
            name = name.strip()
            if region_code in ("pa", "esr"):
                # ftcpenn loads this better than ftcdata ever did because it provides awards data,
                # there's no point in us covering it
                continue
            event_type = cls.EVENT_TYPE_MAP[fevent_type]
            if state.endswith(" SR"):
                event_type = EventType.SUPER_REGIONAL
            elif state.startswith("CMP "):
                event_type = EventType.WORLD_CHAMPIONSHIP

            divno = -1
            # append "Division" to the end of names
            if (ecode.endswith("d0") or ecode.endswith("d1") or ecode.endswith("d2")):
                divno = int(ecode[-1])
                ecode = ecode[:-2]
                #name += " Division"
            if region_code == "txno":
                rcode = "txntx"
            elif ecode == "cmphs":
                rcode = "mihs"
            elif region_code == "txwp":
                rcode = "txph"
            elif region_code == "nynyc":
                rcode = "nyc"
            elif ecode in ("wsr", "nsr", "ssr", "cmptx", "cmpmo"):
                rcode = None
            else:
                rcode = region_code

            region = RegionHelper.region_unabbrev(rcode)

            if "Canada" in name:
                country = "Canada"
            else:
                country = "USA"
            event = Event(key=f"1617{rcode}{ecode}",
                          year=2016, name=name, state_prov=state, country=country,
                          start_date=date, end_date=date, event_type=event_type,
                          region=region,
                          playoff_type=PlayoffType.STANDARD)
            if divno > -1:
                if divno == 0:
                    event.division_keys = [event.key + "1", event.key + "2"]
                else:
                    event.parent_event_key = event.key + "0"
                event.key += str(divno)
            event.event_code = ftcdata_code
            base = f"data/ftc-data/events/1617velv/{region_code.lower()}/1617velv-{ftcdata_code}"

            if os.path.exists(base + "-MatchResultsDetails.html"):
                with open(base + "-MatchResultsDetails.html") as f:
                    matches = ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml'), event.key)
                if os.path.exists(base + "-MatchResultsRaw.csv"):
                    MatchDetailsHelper.parse_ftcdata_csv(matches, base + "-MatchResultsRaw.csv")
            elif os.path.exists(base + "-MatchResults.html"):
                with open(base + "-MatchResults.html") as f:
                    matches = ResultsPageHelper.load_matches(BeautifulSoup(f.read(), 'lxml'), event.key)
            else:
                print("warning: ", event.key, "don't exists!")
                continue

            with open(base + "-Rankings.html") as f:
                rankings = ResultsPageHelper.load_rankings(BeautifulSoup(f.read(), 'lxml'), matches)

            await EventHelper.insert_event(event, matches, rankings, None, tolerate_missing_finals=True, data_source="cheer4ftc ftc-data repository")
            print("loaded " + event.key)

    @classmethod
    async def load(cls):
        pass

async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    #await Event.purge("1516micmp")
    #await FTCDataScraper.load_1516resq()
    #for key in (k['key'] for k in await orm.pool.fetch("SELECT key FROM events WHERE year=2016")):
    #    await Event.purge(key)
    await FTCDataScraper.load_1617velv()
    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

