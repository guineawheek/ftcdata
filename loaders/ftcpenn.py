# need beautifulsoup
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import uvloop
import time
import pprint
import re
import datetime
from models import Event, EventType, Award, AwardType, PlayoffType
from helpers import ResultsPageHelper, year_to_season
from urllib.parse import urlparse
from db.orm import orm


class FTCPennScraper:
    BASE_URL = "http://www.ftcpenn.org"
    TEAM_AWARD = re.compile(r"Team\s+([0-9]+)")
    AWARD_FILTER = re.compile(r"(2nd|3rd)")
    MIN_TIMEOUT = 1
    http = None
    timer = 0

    CODE_MAP = {
        "Eastern": "ea",
        "East": "e",
        "West": "w",
        "Central": "c",
        "Southeastern": "se",
        "Southwestern": "se",
        "Philadelphia": "ph",
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
        now = time.time()
        if now - cls.timer < cls.MIN_TIMEOUT:
            await asyncio.sleep(now - cls.timer)
        now = time.time()
        async with cls.http.get(url) as response:
            return await response.text()


    @classmethod
    async def close_http(cls):
        if cls.http:
            await cls.http.close()

    @classmethod
    async def scrape_event(cls, url, event):

        cls.get_http()
        main_data = await cls.get(url)
        rankings_data = await cls.get(url + "/team-rankings")
        match_details_data = await cls.get(url + "/match-results-details")

        soup = BeautifulSoup(main_data, 'lxml')

        print("Results for", event.key)

        sections = soup.find_all(class_="sites-embed-border-on sites-embed sites-embed-full-width")

        awards = []
        for s in sections:
            title = s.find("h4").text
            if "Award" in title:
                text = cls.AWARD_FILTER.sub("", s.get_text())

                winners = cls.TEAM_AWARD.findall(text)
                award_type = AwardType.to_type(title)
                for i, t in enumerate(winners, 1):
                    a = Award(name=title, award_type=award_type, event_key=event.key, team_key='ftc' + t, award_place=i)
                    awards.append(a)
        pprint.pprint(awards)

        match_details_soup = BeautifulSoup(match_details_data, 'lxml')
        match_details_table = match_details_soup.find("th").find_parent("table")
        matches = ResultsPageHelper.load_match_details(match_details_table, event.key)
        pprint.pprint(matches)

        rankings_soup = BeautifulSoup(rankings_data, 'lxml')
        ranking_table = rankings_soup.find("th").find_parent("table")
        rankings = ResultsPageHelper.load_rankings(ranking_table, matches)
        pprint.pprint(rankings)

        return awards, rankings, matches

    @classmethod
    def mk_event(cls, row, year, event_type):
        name = row[2].find("a").get_text()
        link = row[2].find("a")['href']
        venue = row[3].find("a").get_text()
        website = row[3].find("a")['href']
        if year == 2012:
            address = None
            city = row[4].find("a").get_text().split(",")[-2]
        else:
            city = row[4].get_text().split()[-2][:-1]
            address = row[4].get_text()

        if year < 2014:
            sdate = row[0].get_text().strip()
            # typo workaround
            if sdate == '2/22/2013':
                sdate = '2/22/2014'
            month, day, year_ = sdate.split('/')
            date = datetime.datetime(year=int(year_), month=int(month), day=int(day))
        else:
            _, month, day = row[0].get_text.split()
            year_ = year + 1 if month in ("Jan", "Feb", "Mar") else year
            date = datetime.datetime.strptime("%Y %b %d", f"{year} {month} {int(day):02}")

        season = year_to_season(year)
        event_key = f"{season}pa"
        for keyword in name.split():
            if keyword in cls.CODE_MAP:
                event_key += cls.CODE_MAP[keyword]
        e = Event(key=event_key,
                  year=year,
                  name=name,
                  city=city,
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
    async def load_year(cls, year):
        cls.get_http()
        url = f"http://www.ftcpenn.org/ftc-events/{year}-{year+1}-season"
        async with cls.http.get(url) as response:
            main_data = await response.text()

        page = BeautifulSoup(main_data, 'lxml')
        table = page.find("table", border="1", bordercolor="#888", cellspacing="0")
        for tr in table.find_all("tr"):
            row = [td for td in tr.find_all("td")]
            event_type = row[1].get_text().lower()
            if event_type.find("tournament") >= 0 or event_type.find("championship") >= 0:
                if event_type.find("league"):
                    etype = EventType.LEAGUE_CMP
                elif event.find("championship"):
                    etype = EventType.REGIONAL_CMP
                else:
                    etype = EventType.QUALIFIER
                event, link = cls.mk_event(row, year, etype)
                awards, rankings, matches = cls.scrape_event(link, event)


                #print(*[row[x].get_text() for x in range(1, 5)])


async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()

    await FTCPennScraper.scrape_event("http://www.ftcpenn.org/ftc-events/2012-2013-season/south-eastern-pennsylvania-regional-qualifying-tournament")
    await FTCPennScraper.close_http()
    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

