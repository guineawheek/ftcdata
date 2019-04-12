# need beautifulsoup
from bs4 import BeautifulSoup
import asyncio
import uvloop
import datetime
import logging
import pprint
from models import *
from helpers import OPRHelper, AwardHelper, ResultsPageHelper
from db.orm import orm


class OldChamps:

    @classmethod
    def mk_champs(cls, year, start_date, end_date):
        """generates World Championship events given a start and end date, and division order, and year. Assumes 1champs
        """
        seasons = ["Quad Quandary", "Face Off", "Hot Shot", "Get Over It", "Bowled Over", "Ring It Up", "Block Party",
                   "Cascade Effect", "RES-Q", "Velocity Vortex", "Relic Recovery", "Rover Ruckus"]
        season_name = seasons[year-2007]
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        season = f"{year % 100:02}{(year + 1) % 100:02}"
        # fyear = f"{year}-{(year+1)%1000:02d}"
        if year == 2009:
            city, state_prov, country = "Atlanta", "Georgia", "USA"
            venue = "Georgia Dome"
            address = "1 Georgia Dome Dr, Atlanta, GA 30313"
        elif year < 2013:
            city, state_prov, country = "St. Louis", "Missouri", "USA"
            venue = "Edward Jones Dome"
            address = "701 Convention Plaza, St. Louis, MO 63101"
        else:
            city, state_prov, country = "St. Louis", "Missouri", "USA"
            venue = "Union Station"
            address = "1820 Market Street, St. Louis, MO 63103"
        shared = {
            "year": year,
            "city": city,
            "state_prov": state_prov,
            "country": country,
            "end_date": end_date,
            "event_type": EventType.WORLD_CHAMPIONSHIP,
            "venue": venue,
            "address": address,
            "data_sources": ["USFIRST Website Archives"]
        }

        finals = Event(key=f"{season}cmp0",
                       name=f"FTC {season_name} World Championship - Finals",
                       playoff_type=PlayoffType.BO3_FINALS, 
                       division_keys=[f"{season}cmp1", f"{season}cmp2"],
                       start_date=end_date,
                       **shared)
        franklin = Event(key=f"{season}cmp{2}",
                       name=f"FTC {season_name} World Championship - Franklin Division",
                       playoff_type=PlayoffType.STANDARD, 
                       parent_event_key=f"{season}cmp0", 
                       start_date=start_date,
                       **shared)
        edison = Event(key=f"{season}cmp{1}",
                       name=f"FTC {season_name} World Championship - Edison Division",
                       playoff_type=PlayoffType.STANDARD,
                       parent_event_key=f"{season}cmp0", 
                       start_date=start_date,
                       **shared)
        return (franklin, edison, finals)

    @classmethod
    def load_awards_file(cls, awards_data, year, event_key):
        ret = []
        for line in awards_data.split('\n'):
            if not line:
                continue
            aname, winners = line.split('|')
            atype = AwardType.to_type.get(aname.lower(), "oops!")

            for i, team_data in enumerate(winners.split(','), 1):
                recipient = None
                place = i
                if atype == AwardType.JUDGES:
                    team, sub_name = team_data.split(':')
                    award_name = f"Judge's \"{sub_name}\" Award"
                    place = 1
                elif atype == AwardType.VOL_OF_YEAR or atype == AwardType.COMPASS:
                    team, recipient = team_data.split(':')
                    award_name = AwardType.get_names(atype, year=year)
                else:
                    team = team_data
                    award_name = AwardType.get_names(atype, year=year)

                award = Award(name=award_name, award_type=atype, event_key=event_key, team_key='ftc'+team, recipient_name=recipient, award_place=place)
                award.name += " Winner" if award.award_place == 1 else " Finalist"
                ret.append(award)
        return ret
    
    @classmethod
    async def upsert_all(cls, args):
        async with orm.pool.acquire() as conn:
            for a in args:
                for ent in a:
                    if isinstance(ent, orm.Model):
                        await ent.upsert(conn=conn)
                    else:
                        for ent2 in ent:
                            await ent2.upsert(conn=conn)

    @classmethod
    async def load_2009(cls):
        year = 2009
        with open("data/old_champs/2009-2010/2009CMPresultsandrankings.html") as f:
            data = f.read()
        with open("data/old_champs/2009-2010/awards2") as f:
            awards_data = f.read()

        soup = BeautifulSoup(data, 'lxml')

        tables = list(soup.find_all("table"))
        finals = ResultsPageHelper.load_matches(tables[0], "0910cmp0")
        franklin = ResultsPageHelper.load_matches(tables[1], "0910cmp1")
        edison = ResultsPageHelper.load_matches(tables[2], "0910cmp2")
        franklin_rank = ResultsPageHelper.load_rankings(tables[3], franklin, has_hs=False)
        edison_rank = ResultsPageHelper.load_rankings(tables[4], edison, has_hs=False)
        events = cls.mk_champs(year, "2010-04-14", "2010-04-17")
        awards = cls.load_awards_file(awards_data, year, events[-1].key)

        await cls.finalize([finals, franklin, edison, franklin_rank, edison_rank, events, awards], events, year) 

    @classmethod
    async def load_2010(cls):
        year = 2010
        with open("data/old_champs/2010-2011/2010-2011-ftc-world-championship-get-over-it!-results.html") as f:
            data = f.read()
        with open("data/old_champs/2010-2011/awards") as f:
            awards_data = f.read()

        soup = BeautifulSoup(data, 'lxml')

        tables = list(soup.find_all("table"))
        finals = ResultsPageHelper.load_matches(tables[0], "1011cmp0")
        edison = ResultsPageHelper.load_matches(tables[1], "1011cmp1")
        franklin = ResultsPageHelper.load_matches(tables[2], "1011cmp2")
        edison_rank = ResultsPageHelper.load_rankings(tables[3], edison)
        franklin_rank = ResultsPageHelper.load_rankings(tables[4], franklin)
        events = cls.mk_champs(year, "2011-04-27", "2011-04-30")
        awards = cls.load_awards_file(awards_data, year, events[-1].key)

        await cls.finalize([finals, franklin, edison, franklin_rank, edison_rank, events, awards], events, year) 

    @classmethod
    async def load_2011(cls):
        year = 2011
        with open("data/old_champs/2011-2012/2011-2012FTCCMPResults") as f:
            data = f.read()
        with open("data/old_champs/2011-2012/awards") as f:
            awards_data = f.read()

        soup = BeautifulSoup(data, 'lxml')

        tables = list(soup.find_all("table"))
        finals = ResultsPageHelper.load_matches(tables[3], "1112cmp0")

        franklin = ResultsPageHelper.load_matches(tables[15], "1112cmp1")
        edison = ResultsPageHelper.load_matches(tables[14], "1112cmp2")

        franklin_rank = ResultsPageHelper.load_rankings(tables[13], franklin)
        edison_rank = ResultsPageHelper.load_rankings(tables[12], edison)
        events = cls.mk_champs(year, "2012-04-25", "2012-04-28")
        awards = cls.load_awards_file(awards_data, year, events[-1].key)

        await cls.finalize([finals, franklin, edison, franklin_rank, edison_rank, events, awards], events, year) 

    @classmethod
    async def load_2012(cls):
        year = 2012
        with open("data/old_champs/2012-2013/Match_Results_World Championship_Edison.html") as f:
            edison = ResultsPageHelper.load_matches(BeautifulSoup(f.read(), 'lxml').find("table"), "1213cmp1")
        with open("data/old_champs/2012-2013/Match_Results_World Championship_Franklin.html") as f:
            franklin = ResultsPageHelper.load_matches(BeautifulSoup(f.read(), 'lxml').find("table"), "1213cmp2")
        with open("data/old_champs/2012-2013/finals.html") as f:
            finals = ResultsPageHelper.load_matches(BeautifulSoup(f.read(), 'lxml').find("table"), "1213cmp0")
        with open("data/old_champs/2012-2013/Rankings_World Championship_Edison.html") as f:
            edison_rank = ResultsPageHelper.load_rankings(BeautifulSoup(f.read(), 'lxml').find("table"), edison)
        with open("data/old_champs/2012-2013/Rankings_World Championship_Franklin.html") as f:
            franklin_rank = ResultsPageHelper.load_rankings(BeautifulSoup(f.read(), 'lxml').find("table"), franklin)
        with open("data/old_champs/2012-2013/awards") as f:
            awards = cls.load_awards_file(f.read(), year, '1213cmp0')
        events = cls.mk_champs(year, "2013-04-24", "2013-04-27")

        await cls.finalize([finals, franklin, edison, franklin_rank, edison_rank, events, awards], events, year)

    @classmethod
    async def load_2013(cls):
        year = 2013
        # this is mostly to overwrite tya's names, and to includes awards data (which tya doesn't)
        events = cls.mk_champs(year, "2014-04-24", "2014-04-26")
        for e in events:
            e.data_sources.append("The Yellow Alliance")
        with open("data/old_champs/2013-2014/awards") as f:
            awards = cls.load_awards_file(f.read(), year, '1314cmp0')

        await cls.finalize([events, awards], events, 2013)
    @classmethod
    async def load_2014(cls):
        year = 2014
        # edison
        with open("data/old_champs/2014-2015/MatchResultsDetails_World_Championship_Edison_T.html") as f:
            edison = ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml').find("table"), "1415cmp2")
        with open("data/old_champs/2014-2015/MatchResultsDetails_World_Championship_Edison_Elim.html") as f:
            edison.extend(ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml').find("table"), "1415cmp2"))
        # franklin
        with open("data/old_champs/2014-2015/MatchResultsDetails_World_Championship_Franklin_T.html") as f:
            franklin = ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml').find("table"), "1415cmp1")
        with open("data/old_champs/2014-2015/MatchResultsDetails_World_Championship_Franklin_Elim.html") as f:
            franklin.extend(ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml').find("table"), "1415cmp1"))
        # finals
        with open("data/old_champs/2014-2015/MatchResultsDetails_World_Championship_Finals.html") as f:
            finals = ResultsPageHelper.load_match_details(BeautifulSoup(f.read(), 'lxml').find("table"), "1415cmp0")
        # rankings
        with open("data/old_champs/2014-2015/Rankings_World_Championship_Edison.html") as f:
            edison_rank = ResultsPageHelper.load_rankings(BeautifulSoup(f.read(), 'lxml').find("table"), edison)
        with open("data/old_champs/2014-2015/Rankings_World_Championship_Franklin.html") as f:
            franklin_rank = ResultsPageHelper.load_rankings(BeautifulSoup(f.read(), 'lxml').find("table"), franklin)

        with open("data/old_champs/2014-2015/awards") as f:
            awards = cls.load_awards_file(f.read(), year, '1415cmp0')
        events = cls.mk_champs(year, "2015-04-22", "2015-04-25")

        await cls.finalize([finals, franklin, edison, franklin_rank, edison_rank, events, awards], events, year)
    @classmethod
    async def finalize(cls, objects, events, year):
        await cls.upsert_all(objects)
        logging.info(f"finalize({year}): Calculating OPRs....")
        await asyncio.gather(*[OPRHelper.update_oprs(event.key) for event in events])
        logging.info(f"finalize({year}): Generating winning/finalist awards...")
        await asyncio.gather(*[AwardHelper.generate_winners_finalists(e, fail_silent=True) for e in events])
        logging.info(f"finalize({year}): generating EventParticipants...")
        await EventParticipant.generate(year)

    @classmethod
    def read_table(cls, table):
        return [[td.get_text() for td in tr.find_all("td")] for tr in table.find_all("tr")]

    @classmethod
    async def load(cls):
        MAX_YEAR = 2015
        for i in range(2009, MAX_YEAR):
            if hasattr(cls, f'load_{i}'):
                await getattr(cls, f'load_{i}')()
            print("...", i)


async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    print("Loading old championship data...")
    await OldChamps.load()

    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

