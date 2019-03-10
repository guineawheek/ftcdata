#!/home/l/li/liuderek/remote/web-venv/bin/python3
import json
import pickle
import gzip
import requests
import os
from pprint import pprint as p

# we need to know what CURRENT_YEAR is so we can make jokes
CURRENT_YEAR = 2018
fname = lambda y: f"{y}.pickle"

os.chdir("/home/l/li/liuderek/teamdata")

teams = {}

""" schema:
Team: 
    number: int,
    rookie_year: int,
    events: [Event],
    awards: [Award],
    seasons: [Season],


Event: {
    name: str,
    season: int,
    region: str,
}

Season: {
    year: int,
    name: str,
    org: str,
    motto: str,
    website: str,
    location: {lat, lon}
    city: str,
    country: str,
    postal_code: str,
    state_prov: str,
"""


for y in range(CURRENT_YEAR, 2006, -1):
    if y == CURRENT_YEAR:
        print(f"----- downloading {y} data")
        r = requests.get("https://es01.usfirst.org/teams/_search?size=30000&from=0&source={%22query%22:{%22filtered%22:{%22query%22:{%22bool%22:{%22must%22:[{%22bool%22:{%22should%22:[[{%22match%22:{%22team_type%22:%22FTC%22}}]]}},{%22bool%22:{%22should%22:[[{%22match%22:{%22profile_year%22:" + str(y) + "}}]]}}]}}}},%22sort%22:%22team_number_yearly%22}", verify=False)
        data = r.json() 
    else:
        print(f"----- reading {fname(y)}")
        with open(fname(y), "rb") as f:
            data = pickle.load(f)

    # writing it out takes precious disk space
    if y == CURRENT_YEAR:
        print(f"----- writing {fname(y)}")
        with open(fname(y), "wb") as f:
            pickle.dump(data, f, protocol=4)
    
    print(f"----- parsing {fname(y)}")
    for t in data['hits']['hits']:
        s = t["_source"]
        number = int(s["team_number_yearly"])

        # these numbers don't list an event name or season from their awards 
        # in Far East championships; this occurs in the 2012-2013 record.
        #if number in [6907, 6908, 6919, 6922, 6923]: continue
        print(f"loading team {number}")

        if number not in teams:
            # populate the team static info and the events/awards tables
            teams[number] = {
                "number": number,
                "rookie_year": int(s.get("team_rookieyear", y)),
                "events": [
                    {
                        "name": i["event_name"],
                        "season": int(i["event_season"])
                    } for i in s["events"]
                ],
                # 6907, 6908, 6919, 6922, and 6923 don't have event name or season listed
                "awards": [
                    {
                        "award": i["award"],
                        "event": i.get("event_name", f'{s["team_country"]} FTC Championship'),
                        "region": i["eventcode_cache"],
                        "season": int(i.get("event_season", y))
                    } for i in s["awards"]
                ],
                "seasons": [] # this table gets populated later
            } 

        teams[number]["seasons"].append({
            "year": int(s["profile_year"]),
            "name": s.get("team_nickname", f"Team {number}"),
            "org": s.get("team_name_calc", ""),
            "motto": s.get("team_motto", ""),
            "website": s.get("team_web_url", ""),
            "location": [s["location"][0]["lat"], s["location"][0]["lon"]],
            "city": s["team_city"],
            "country": s["team_country"],
            "postal_code": s["team_postalcode"],
            "state_prov": s.get("team_stateprov", ""),
        })
#with open("ftc_teams.json", "w") as f:
#    json.dump(teams, f, ensure_ascii=False, sort_keys=True, indent=2)

with gzip.open("/home/l/li/liuderek/teamdata/ftc_teams.pickle.gz", "wb") as f:
    # protocol 4 doesn't work with py < 3.4
    pickle.dump(teams, f, protocol=4)

with open("/home/l/li/liuderek/public_html/ftc_teams.json", "w") as f:
    json.dump(teams, f)

# this is bad but idc
#os.system("cp ~/teamdata/ftc_teams.pickle.gz ~/public_html/ftc/teams.pickle.gz")
