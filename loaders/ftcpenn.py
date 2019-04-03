# need beautifulsoup
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import uvloop
import time
import pprint
import re
import datetime
import unicodedata
from models import Event, EventType, Award, AwardType, PlayoffType
from helpers import ResultsPageHelper, EventHelper, year_to_season
from urllib.parse import urlparse
from db.orm import orm

__all__ = ["FTCPennScraper", "ESRScraper"]

def mkdate(year, month, day):
    return datetime.datetime(year=year, month=month, day=day)

class FTCPennScraper:
    BASE_URL = "http://www.ftcpenn.org"
    TEAM_AWARD = re.compile(r"Team\s+([0-9]+)")
    AWARD_FILTER = re.compile(r"(2nd|3rd)")
    MIN_TIMEOUT = 1
    http = None
    timer = 0

    CODE_MAP = {
        "Eastern": "ea",
        "Blue": "bw",
        "Maroon": "mw",
        "Green": "gg",
        "East": "e",
        "West": "w",
        "South": "s",
        "Central": "c",
        "Southeastern": "se",
        "Southwestern": "sw",
        "Philadelphia": "ph",
        "League": "lcmp",
        "Pittsburgh": "pi",
        "Rookies": "rk",
        "Lehigh": "lv",
        "Heart": "ihr",
        "Tricks": "ht",
    }

    @classmethod
    def get_http(cls):
        if not cls.http:
            cls.http = aiohttp.ClientSession(headers={"User-Agent": "FTCData Project FTCPenn Scraper"})
        return cls.http

    @classmethod
    async def get(cls, url):
        cls.get_http()
        now = time.time()
        if now - cls.timer < cls.MIN_TIMEOUT:
            await asyncio.sleep(now - cls.timer)
        now = time.time()
        async with cls.http.get(url) as response:
            return unicodedata.normalize("NFKD", await response.text())


    @classmethod
    async def close_http(cls):
        if cls.http:
            await cls.http.close()

    @classmethod
    def load_awards(cls, soup, event):
        sections = soup.find_all(class_="sites-embed-border-on sites-embed sites-embed-full-width")

        awards = []
        for s in sections:
            title = s.find("h4").text
            if "Award" in title:
                text = cls.AWARD_FILTER.sub("", s.get_text())
                # replacing Place and Winner: with Team compensates for lack of prefixing in some
                # ftcpenn pages
                text = re.sub(r"Place:?", "Team ", text)
                text = re.sub(r"Winner:?", "Team ", text)
                # there's a case in 1415pacmp that fools our award detector.
                # oops!
                text = re.sub(r"Teal\s+Team\s+6", "", text)
                title = re.sub(r"Award.*$", "Award", title)

                winners = cls.TEAM_AWARD.findall(text)
                award_type = AwardType.get_type(title)
                for i, t in enumerate(winners, 1):
                    a = Award(name=title, award_type=award_type, event_key=event.key, team_key='ftc' + t, award_place=i)
                    if i == 1:
                        a.name += " Winner"
                    else:
                        a.name += " Finalist"
                    awards.append(a)
        return awards

    @classmethod
    async def scrape_event(cls, url, event):
        main_data = await cls.get(url)
        rankings_data = await cls.get(url + "/team-rankings")
        match_details_data = await cls.get(url + "/match-results-details")

        soup = BeautifulSoup(main_data, 'lxml')

        #print("Results for", event.key)
        awards = cls.load_awards(soup, event)

        #pprint.pprint(awards)

        match_details_soup = BeautifulSoup(match_details_data, 'lxml')
        match_details_table = match_details_soup.find("th").find_parent("table")
        matches = ResultsPageHelper.load_match_details(match_details_table, event.key)
        #pprint.pprint(matches)

        rankings_soup = BeautifulSoup(rankings_data, 'lxml')
        ranking_table = rankings_soup.find("th").find_parent("table")
        rankings = ResultsPageHelper.load_rankings(ranking_table, matches)
        #pprint.pprint(rankings)

        return awards, rankings, matches

    @classmethod
    def mk_event(cls, row, year, event_type):
        name = row[2].find("a").get_text()
        link = row[2].find("a")['href']
        venue = row[3].find("a").get_text().strip()
        website = row[3].find("a")['href']
        if year == 2012:
            address = None
            city = row[4].get_text().split(",")[-2]
        else:
            if year < 2017:
                city = row[4].get_text().split()[-2][:-1]
            else:
                # 2017+ has a "zipcode" field
                city = row[4].get_text().split()[-3][:-1]
            address = row[4].get_text().strip()
            if city.startswith("Road"):
                city = city[4:]

        if year < 2014:
            sdate = row[0].get_text().strip()
            # typo workaround
            if sdate == '2/22/2013':
                sdate = '2/22/2014'
            month, day, year_ = sdate.split('/')
            date = datetime.datetime(year=int(year_), month=int(month), day=int(day))
        else:
            month, day = row[0].get_text().split()[1:3]
            year_ = year + 1 if month in ("Jan", "Feb", "Mar") else year
            date = datetime.datetime.strptime(f"{year_} {month} {int(day):02}", "%Y %b %d")

        season = year_to_season(year)
        event_key = f"{season}pa"
        if name.startswith("Central Pennsylvania"):
            event_key += "ce"
        else:
            for keyword in name.split():
                if keyword in cls.CODE_MAP:
                    event_key += cls.CODE_MAP[keyword]
        if event_type == EventType.REGIONAL_CMP:
            event_key += "cmp"
        e = Event(key=event_key,
                  year=year,
                  name=name.strip(),
                  city=city.strip(),
                  state_prov="Pennsylvania",
                  country="USA",
                  start_date=date,
                  end_date=date,
                  event_type=event_type,
                  venue=venue,
                  address=address,
                  website=website,
                  playoff_type=PlayoffType.STANDARD)
        #TODO: slots, host?

        return e, link

    @classmethod
    async def load_meets(cls, year):
        base_url = f"http://www.ftcpenn.org/ftc-events/{year}-{year+1}-season"
        if year == 2014:
            match_url = base_url + "/philadelphia-area-league-meets/match-results-details"
            rankings_url = base_url + "/philadelphia-area-league-meets/team-rankings"
            match_tables = BeautifulSoup(await cls.get(match_url), 'lxml').find(
                class_="sites-layout-tile sites-tile-name-content-1"
            ).find_all("table")
            rankings_tables = BeautifulSoup(await cls.get(rankings_url), 'lxml').find(
                class_="sites-layout-tile sites-tile-name-content-1"
            ).find_all("table")
            dates = [mkdate(2014, 12, 10), mkdate(2014, 12, 11), mkdate(2015, 1, 14), mkdate(2015, 1, 15)]
            for i, match_table, rankings_table in zip(range(1, 5), match_tables, rankings_tables):
                event_key = f"1415paphlm{i}"
                print("Processing", event_key)
                event = Event(key=event_key,
                              year=year,
                              name=f"Philadelphia Area League - Meet {i}",
                              city="Philadelphia", state_prov="Pennsylvania", country="USA",
                              start_date=dates[i-1],
                              end_date=dates[i-1],
                              event_type=EventType.MEET,
                              venue="Temple University College of Engineering Building",
                              address="1947 N 12th St. Philadelphia, PA",
                              website="https://www.temple.edu",
                              playoff_type=PlayoffType.STANDARD)
                matches = ResultsPageHelper.load_match_details(match_table, event.key)
                rankings = ResultsPageHelper.load_rankings(rankings_table, matches)
                await EventHelper.insert_event(event, matches, rankings, None)


    @classmethod
    async def load_year(cls, year):
        url = f"http://www.ftcpenn.org/ftc-events/{year}-{year+1}-season"
        main_data = await cls.get(url)

        page = BeautifulSoup(main_data, 'lxml')
        # replace <br> with newlines; this fixes some get_text() curiosities
        for br in page.find_all("br"):
            br.replace_with("\n")
        table = page.find("table", border="1", bordercolor="#888", cellspacing="0")
        for tr in table.find_all("tr"):
            row = [td for td in tr.find_all("td")]
            event_type = row[1].get_text().lower()
            if event_type.find("tournament") >= 0 or event_type.find("championship") >= 0:
                #print(event_type)
                if event_type.find("league") >= 0:
                    etype = EventType.LEAGUE_CMP
                    # TODO: implement a league datatype; for now, we skip the league champs
                    if year != 2015:
                        # we parse the philly league champ like normal lol
                        continue
                elif event_type.find("championship") >= 0:
                    etype = EventType.REGIONAL_CMP
                else:
                    etype = EventType.QUALIFIER
                event, link = cls.mk_event(row, year, etype)
                if year == 2017 and event.key not in ("1718palv", "1718pacmp"):
                    # TOA has more detailed data than ftcpenn does because they have zips with
                    # real breakdowns
                    continue
                if year == 2018 and event.key.startswith("1819pacmp") or event.key == "1819pasw":
                    # TOA has pa champs, and it's a multidiv event, so we abort here too
                    # also pasw just isn't lmao
                    continue
                print("Processing " + event.key)
                awards, rankings, matches = await cls.scrape_event(link, event)
                await EventHelper.insert_event(event, matches, rankings, awards)

    @classmethod
    async def load(cls):
        # min 2012
        for i in range(2017, 2019):
            await cls.load_year(i)

class ESRScraper(FTCPennScraper):
    # same website, right?
    @classmethod
    async def load(cls):
        for i in range(2012, 2018):
            await cls.load_year(i)

    @classmethod
    async def load_year(cls, year):
        if year not in range(2013, 2018):
            raise ValueError("invalid year!")
        url = f"http://www.ftceast.org/tournament/tournament-results/{year}-{year+1}-Results"
        main_data = await cls.get(url)
        if year == 2013:
            date = datetime.datetime(year=2014, month=4, day=3)
        else:
            date = datetime.datetime(year=year+1, month=3, day=2033-year)
            url = url.lower()

        common_info = {
            "year": year,
            "city": "Scranton",
            "state_prov": "Pennsylvania",
            "country": "USA",
            "start_date": date,
            "end_date": date + datetime.timedelta(days=2),
            "event_type": EventType.SUPER_REGIONAL,
            "venue": "University of Scranton",
            "address": "",
            "website": "http://www.ftceast.org",
        }
        season = f"{year % 100:02}{(year + 1) % 100:02}"
        finals = Event(key=f"{season}esr0",
                       name=f"FTC East Super Regional Championship",
                       playoff_type=PlayoffType.BO3_FINALS,
                       division_keys=[f"{season}esr1", f"{season}esr2"],
                       **common_info)
        hopper = Event(key=f"{season}esr1",
                       name=f"FTC East Super Regional Championship - Hopper Division",
                       playoff_type=PlayoffType.STANDARD,
                       parent_event_key=f"{season}esr0",
                       **common_info)
        tesla = Event(key=f"{season}esr2",
                       name=f"FTC East Super Regional Championship - Tesla Division",
                       playoff_type=PlayoffType.STANDARD,
                       parent_event_key=f"{season}esr0",
                       **common_info)
        soup = BeautifulSoup(main_data, 'lxml')

        #print("Results for", finals.key)
        suffix = "" if year == 2013 else "-details"
        rank_page = "-ranking-list" if year == 2013 else "-team-rankings"
        awards = cls.load_awards(soup, finals)
        finals_details_data = await cls.get(url + "/finals-match-results" + suffix)
        match_details_table = BeautifulSoup(finals_details_data, 'lxml').find("th").find_parent("table")
        finals_matches = ResultsPageHelper.load_match_details(match_details_table, finals.key)

        hopper_details_data = await cls.get(url + "/hopper-match-results" + suffix)
        match_details_table = BeautifulSoup(hopper_details_data, 'lxml').find("th").find_parent("table")
        hopper_matches = ResultsPageHelper.load_match_details(match_details_table, hopper.key)

        hopper_rank_data = await cls.get(url + "/hopper" + rank_page)
        hopper_rank_table = BeautifulSoup(hopper_rank_data, 'lxml').find("th").find_parent("table")
        hopper_rank = ResultsPageHelper.load_rankings(hopper_rank_table, hopper_matches)

        tesla_details_data = await cls.get(url + "/tesla-match-results" + suffix)
        match_details_table = BeautifulSoup(tesla_details_data, 'lxml').find("th").find_parent("table")
        tesla_matches = ResultsPageHelper.load_match_details(match_details_table, tesla.key)

        tesla_rank_data = await cls.get(url + "/tesla" + rank_page)
        tesla_rank_table = BeautifulSoup(tesla_rank_data, 'lxml').find("th").find_parent("table")
        tesla_rank = ResultsPageHelper.load_rankings(tesla_rank_table, tesla_matches)

        await EventHelper.insert_event(hopper, hopper_matches, hopper_rank, None)
        await EventHelper.insert_event(tesla, tesla_matches, tesla_rank, None)
        await EventHelper.insert_event(finals, finals_matches, None, awards, divisions=[hopper, tesla])

async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    await Event.purge("1415paphlm1")
    #await FTCPennScraper.load_year(2015)
    await FTCPennScraper.load_meets(2014)
    #await FTCPennScraper.load()
    await FTCPennScraper.close_http()
    #await ESRScraper.load_year(2017)
    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

