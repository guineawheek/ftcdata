# need beautifulsoup
from bs4 import BeautifulSoup
from models import Event
import pprint
import re
import aiohttp

class FTCPennScraper:
    BASE_URL = "http://www.ftcpenn.org"
    TEAM_AWARD = re.compile(r"Team\s+([0-9]+)")
    AWARD_FILTER = re.compile(r"(2nd|3rd)")

    @classmethod
    async def scrape_event(cls, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                main_data = await response.text()
            async with session.get(url + "/team-rankings") as response:
                rankings_data = await response.text()
            async with session.get(url + "/match-results-details") as response:
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
