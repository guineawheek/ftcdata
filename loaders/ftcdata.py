import asyncio
import uvloop
import csv
import pprint
import re
import datetime
import unicodedata

from bs4 import BeautifulSoup
from loaders.old_champs import OldChamps
from models import Event, EventType, Award, AwardType, PlayoffType
from helpers import ResultsPageHelper, EventHelper, RegionHelper, year_to_season
from db.orm import orm

__all__ = ["FTCDataScraper"]

class FTCDataScraper:
    EVENT_TYPE_MAP = {
        "Qualifying Tournament": EventType.QUALIFIER,
        "Super Regional Championship": EventType.SUPER_REGIONAL,
        "League Championship": EventType.LEAGUE_CMP,
        "Championship Tournament": EventType.REGIONAL_CMP,
        "World Championship": EventType.WORLD_CHAMPIONSHIP
    }

    @classmethod
    async def load_1516resq(cls):
        with open("data/ftc-data/events/1516resq/1516resq-event-list.csv") as f:
            csv_reader = csv.reader(f.read().split("\n"))
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
                await finals.upsert()
            elif event_type == EventType.SUPER_REGIONAL:
                rcode = region_code
            else:
                if state == "California":
                    if "Qualifying Tournament" in name:
                        region, rcode = "California NorCal", "canc"
                    else:
                        region, rcode= "California Los Angeles", "cala"
                elif state == "Massachusettes":
                    # typo in data
                    region, rcode = "Massachusetts", "ma"
                elif state == "New York":
                    if "Hudson Valley" in name:
                        region, rcode = "New York Hudson Valley", "nyhv"
                    else:
                        region, rcode = "New York Excelsior", "nyex"
                elif state.startswith("Texas"):
                    state = "Texas"
                    if ecode in {"a2", "ac", "au", "ki", "cmpal"}:
                        region, rcode = "Texas Alamo", "txal"
                    elif ecode in {"cmplld", "cmplwh", "cmpse", "hf"}:
                        region, rcode = "Texas Southeast", "txse"
                    else: #ecode in {"cmplep", "cmplpps"}:
                        region, rcode = "Texas Panhandle", "txph"
                elif state == "Michigan":
                    region, rcode = "Michigan Highschool", "mihs"
                else:
                    region = state
                    rcode = region_code
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

            await EventHelper.insert_event(event, matches, rankings, None, tolerate_missing_finals=True)
            print("loaded " + event.key)


    @classmethod
    async def load(cls):
        pass

async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    await Event.purge("1516micmp")
    await FTCDataScraper.load_1516resq()
    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

