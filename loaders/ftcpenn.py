# need beautifulsoup
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import asyncpg
import uvloop
import datetime
import pprint
import re
from models import Event, EventType, Award, Match, MatchScore
from helpers import LocationHelper, ChampSplitHelper
from db.orm import orm


class FTCPennScraper:
    BASE_URL = "http://www.ftcpenn.org"
    TEAM_AWARD = re.compile(r"Team\s+([0-9]+)")
    AWARD_FILTER = re.compile(r"(2nd|3rd)")
    http = None

    @classmethod
    def get_http(cls):
        if not cls.http:
            cls.http = aiohttp.ClientSession(headers={"User-Agent": "FTCData Project FTCPenn Scraper"})
        return cls.http

    @classmethod
    async def scrape_event(cls, url):
        cls.get_http()
        async with cls.http.get(url) as response:
            main_data = await response.text()
        async with cls.http.get(url + "/team-rankings") as response:
            rankings_data = await response.text()
        async with cls.http.get(url + "/match-results-details") as response:
            match_details_data = await response.text()

        soup = BeautifulSoup(main_data, 'lxml')

        sections = soup.find_all(class_="sites-embed-border-on sites-embed sites-embed-full-width")

        awards = {}

        for s in sections:
            title = s.find("h4").text
            if "Award" in title:
                winners = []
                text = cls.AWARD_FILTER.sub("", s.get_text())

                res = cls.TEAM_AWARD.findall(text)
                awards[title] = res
                #print(title, res)

        rankings_soup = BeautifulSoup(rankings_data, 'lxml')
        ranking_table = rankings_soup.find("th").find_parent("table")
        rankings = [[td.get_text() for td in tr.find_all("td")] for tr in ranking_table.find_all("tr")]
        #pprint.pprint(rankings)

        match_details_soup = BeautifulSoup(match_details_data, 'lxml')
        match_details_table = match_details_soup.find("th").find_parent("table")
        match_details = [[td.get_text() for td in tr.find_all("td")] for tr in match_details_table.find_all("tr")]
        #pprint.pprint(match_details)

        return awards, rankings, match_details
    
    @classmethod
    async def get_events(cls, year):
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
                if "qualifying" in event_type:
                    pass
                    
                print(row[1], row[2], row[3], row[4])


async def main():
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()


    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())

