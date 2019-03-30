# need beautifulsoup
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import asyncpg
import uvloop
import datetime
import pprint
import logging
import re
from models import *
from helpers import OPRHelper, AwardHelper
from db.orm import orm


class OldChamps:

    @classmethod
    def get_http(cls):
        if not cls.http:
            cls.http = aiohttp.ClientSession(headers={"User-Agent": "FTCData Project FTCPenn Scraper"})
        return cls.http

    @classmethod
    def mk_match(cls, event_key, mname, result, red_a, blue_a):
        res_map = {"R": "red", "B": "blue", "T": "tie"}
        match_code = mname.split('-')
        comp_level = match_code[0].lower() 
        mnum = int(match_code[-1])
        set_number = int(match_code[1]) if len(match_code) == 3 else None
        match = Match(event_key=event_key, comp_level=comp_level, match_number=mnum, set_number=set_number)
        scores, winner = result.split() 
        red_score, blue_score = scores.split('-')
        match.winner = res_map[winner]
        match.gen_keys() 

        red = MatchScore(key=match.red_key, alliance_color="red", event_key=event_key, match_key=match.key, dqed=[], total=int(red_score), teams=[f'ftc{s.strip("*")}' for s in red_a])
        red.surrogates = [f'ftc{s.strip("*")}' for s in red_a if s.endswith('*')]

        blue = MatchScore(key=match.blue_key, alliance_color="blue", event_key=event_key, match_key=match.key, dqed=[], total=int(blue_score), teams=[f'ftc{s.strip("*")}' for s in blue_a])
        blue.surrogates = [f'ftc{s.strip("*")}' for s in blue_a if s.endswith('*')]

        return (match, red, blue)

    @classmethod
    def load_matches(cls, table, event_key):
        red_a, blue_a = None, None
        mname, result = "", ""
        matches = []
        for tr in table.find_all("tr"):
            td = [td.get_text() for td in tr.find_all("td")]
            if len(td) == 4:
                if red_a:
                    matches.append(cls.mk_match(event_key, mname, result, red_a, blue_a))
                mname = td[0]
                result = td[1]
                red_a, blue_a = [td[2]], [td[3]]
            elif len(td) == 2:
                red_a.append(td[0])
                blue_a.append(td[1])
        matches.append(cls.mk_match(event_key, mname, result, red_a, blue_a))
        return matches

    @classmethod
    def load_rankings(cls, table, matches):
        event_key = matches[0][0].event_key
        high_scores, wlt = cls.load_rank_data(matches) 
        ret = []
        first = True
        for tr in table.find_all("tr"):
            if first:
                first = False
                continue
            td = [td.get_text() for td in tr.find_all("td")]
            tkey = "ftc" + td[1]
            twlt = wlt[tkey]
            r = Ranking(event_key=event_key, team_key=tkey, qp_rp=int(td[3]), rp_tbp=int(td[4]), high_score=high_scores.get(tkey, 0), wins=twlt[0], losses=twlt[1], ties=twlt[2], dqed=0, played=int(td[5]), rank=int(td[0]))
            ret.append(r)
        return ret

    @classmethod
    def load_rank_data(cls, matches):
        teams = set()
        for m, red, blue in matches:
            teams.update(red.teams)
            teams.update(blue.teams)

        high_scores = {t: 0 for t in teams}
        wlt = {t: [0, 0, 0] for t in teams}
        def update_wlt(wlt, idx, teams):
            for team in teams:
                wlt[team][idx] += 1
            
        for m, red, blue in matches:
            if m.comp_level != 'q':
                continue
            for team in red.teams:
                if high_scores[team] < red.total:
                    high_scores[team] = red.total
            for team in blue.teams:
                if high_scores[team] < blue.total:
                    high_scores[team] = blue.total
            if m.winner == 'red':
                ridx, bidx = 0, 1
            elif m.winner == 'blue':
                ridx, bidx = 1, 0
            else:
                ridx, bidx = 1, 1

            update_wlt(wlt, ridx, red.teams)
            update_wlt(wlt, bidx, blue.teams)
        return high_scores, wlt

    @classmethod
    def mk_champs(cls, year, start_date, end_date): 
        start_date = datetime.datetime.strptime(start_date, "%Y-%M-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%M-%d")
        season = f"{year % 100:02}{(year + 1) % 100:02}"
        fyear = f"{year}-{(year+1)%1000:02d}"
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
           "start_date": start_date,
           "end_date": end_date,
           "event_type": EventType.WORLD_CHAMPIONSHIP,
       }

        finals = Event(key=f"{season}cmp0",
                       name="FIRST Tech Challenge World Championship - Finals",
                       playoff_type=PlayoffType.BO3_FINALS, 
                       division_keys=[f"{season}cmp1", f"{season}cmp2"],
                       **shared)
        franklin = Event(key=f"{season}cmp1", 
                       name="FIRST Tech Challenge World Championship - Franklin Division",
                       playoff_type=PlayoffType.STANDARD, 
                       parent_event_key=f"{season}cmp0", 
                       **shared)
        edison = Event(key=f"{season}cmp2", 
                       name="FIRST Tech Challenge World Championship - Edison Division",
                       playoff_type=PlayoffType.STANDARD,
                       parent_event_key=f"{season}cmp0", 
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
                    award_name = f"Judge's ({sub_name}) Award"
                    place = 1
                elif atype == AwardType.VOL_OF_YEAR:
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
    def load_awards_2009(cls, awards_data, event_key):
        #TODO: volunteer of year, compass award
        a = ""
        c = 1
        judges = False
        awards = []
        for line in awards_data.split('\n'):
            bits = line.split()
            if not len(bits):
                continue
            if bits[0] not in ("Winner:", "Finalist:"):
                a = line
                c = 1
                if bits[0] == "Judge's":
                    judges = True
            else:
                team = "ftc" + bits[2]
                award_type = AwardType.to_type.get(a.lower(), "oops!")
                award = Award(name=AwardType.get_names(award_type, year=2009) if not judges else f"Judge's ({' '.join(bits[3:-1])}) Award",
                          award_type=award_type,
                          award_place=c if not judges else 1,
                          event_key=event_key,
                          team_key=team,
                          recipient_name=None)
                award.name += " Winner" if award.award_place == 1 else " Finalist"
                awards.append(award)
                c += 1
        # he won volunteer of the year, so i hardcoded him in
        awards.append(Award(name=AwardType.get_names(AwardType.VOL_OF_YEAR, year=2009), award_type=AwardType.VOL_OF_YEAR, award_place=1, event_key=event_key, team_key='ftc0', recipient_name="Vince Frascella"))
        return awards
    
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

        tables = list(soup.find_all("table"))#[tbody.find_parent("table") for tbody in soup.find_all("tbody")]
        finals = cls.load_matches(tables[0], "0910cmp0")
        franklin = cls.load_matches(tables[1], "0910cmp1")
        edison = cls.load_matches(tables[2], "0910cmp2")
        franklin_rank = cls.load_rankings(tables[3], franklin)
        edison_rank = cls.load_rankings(tables[4], edison)
        events = cls.mk_champs(year, "2010-04-14", "2010-04-17")
        #awards = cls.load_awards_2009(awards_data, events[-1].key)
        awards = cls.load_awards_file(awards_data, year, events[-1].key)

        await cls.finalize([finals, franklin, edison, franklin_rank, edison_rank, events, awards], events, year) 

    @classmethod
    async def load_2010(cls):
        year = 2010
        with open("data/old_champs/2010-2011/2010-2011-ftc-world-championship-get-over-it!-results.html") as f:
            data = f.read()
        with open("data/old_champs/2010-2011/2010-2011-ftc-world-championship-award-winners.html") as f:
            awards_data = f.read()


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
        MAX_YEAR = 2010
        for i in range(2009, MAX_YEAR):
            await getattr(cls, f'load_{i}')()


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

