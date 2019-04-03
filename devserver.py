from sanic import Sanic
from sanic.response import json, html
from sanic.exceptions import abort

from jinja2 import Environment, FileSystemLoader, ModuleLoader, select_autoescape
from template_engine import jinja2_engine
from db.orm import orm
from models import Team, Event, Ranking, Award, AwardType, EventParticipant, EventType
from helpers import MatchHelper, BracketHelper, AwardHelper, EventHelper
import uvloop
import runtime
import re
import logging

import asyncio
#env = Environment(
#    loader=FileSystemLoader('templates_jinja2'),
#    autoescape=select_autoescape(['html', 'xml'])
#)
#all_templates = [t.name for t in env.list_templates()]
env = jinja2_engine.get_jinja_env(force_filesystemloader=True)

app = Sanic()
app.static("/javascript", "./static/compiled/javascript")
app.static("/css", "./static/compiled/css")
app.static("/images", "./static/images")

def format_year(year):
    return f"{year}-{(year+1)%1000:02d}"

def format_season(season):
    return format_year(season_to_year(season))

def year_to_season(year):
    return f"{year % 100:02}{(year + 1) % 100:02}"

def season_to_year(season):
    season = int(season)
    return (season % 100) - 1 + 2000

@app.listener("before_server_start")
async def setup_db(app, loop):
    await runtime.setup_orm(orm)

@app.listener("after_server_stop")
async def close_db(app, loop):
    await orm.close()

@app.route("/favicon.ico")
async def favicon(request):
    abort(404)

@app.route("/<name>")
async def template(request, name):
    if not name.endswith(".html"):
        name += ".html"
    return html(env.get_template(name).render({}))

@app.route("/team/<number:int>")
async def teams(request, number):
    return await teams_year(request, number, None)

@app.route("/team/<number:int>/<season:int>")
async def teams_year(request, number, season):
    if season is None:
        team = await Team.most_recent(number=number)
        year = team.year
    else:
        year = season_to_year(season)
        team = await Team.select_one(properties={'number': number, 'year': year})
    if not team:
        abort(404)
    years = [r["year"] for r in await orm.pool.fetch("SELECT year FROM teams WHERE number=$1 ORDER BY year", number)]

    season_wlt = await MatchHelper.get_wlt(team.key, year=year)
    participation = await EventHelper.get_team_events(team.key, year)

    return html(env.get_template("team_details.html").render({
        "year": year,
        "years": years,
        "team": team,
        "format_year": format_year,
        "year_to_season": year_to_season,
        "region_name": team.region,
        "season_wlt": season_wlt,
        "participation": participation,
        "max_year": 2018,
        "last_competed": years[-1]
    }))

@app.route("/team/<number:int>/history")
async def teams_history(request, number):
    year = await orm.pool.fetchval("SELECT max(year) FROM teams WHERE number=$1", number)
    team = await Team.most_recent(number)
    if not team:
        abort(404)
    team_events = await EventParticipant.select(properties={"team_key": team.key})
    event_awards = []
    for ep in team_events:
        if not (ep.has_awards or ep.has_matches):
            continue
        event = await Event.select_one(properties={"key": ep.event_key})
        if not ep.has_awards:
            event_awards.append((event, None))
        else:
            event_awards.append((event, await AwardHelper.sorted_awards(
                await Award.select(properties={"event_key": ep.event_key, "team_key": team.key}))))
    return html(env.get_template("team_history.html").render({
        "team": team,
        "event_awards": sorted(event_awards, key=lambda x: x[0].start_date),
        "max_year": 2018,
        "last_competed": team.year
    }))

@app.route("/teams")
async def teams_list_default(request):
    return await teams_list(request, 1)

@app.route("/teams/<page:int>")
async def teams_list(request, page):
    MAX_LABEL = 17
    if page < 1 or page > MAX_LABEL:
        abort(404)
    # improved from tba
    page_labels = ['1-999'] + [f"{x * 1000}'s" for x in range(1, MAX_LABEL)]
    cur_page_label = page_labels[page - 1]

    teams = await Team.team_list(k=page)
    num_teams = len(teams)
    teams_a = teams[:num_teams//2]
    teams_b = teams[num_teams//2:]
    return html(env.get_template('team_list.html').render({
        'teams_a': teams_a,
        'teams_b': teams_b,
        'num_teams': num_teams,
        'page_labels': page_labels,
        'cur_page_label': cur_page_label,
        'current_page': page
    }))

@app.route("/event/<event_key>")
async def event_details(request, event_key):
    event = await Event.select_one(properties={'key': event_key})
    if event is None:
        abort(404)
    if event.parent_event_key:
        parent_event = await Event.select_one(properties={'key': event.parent_event_key})
    else:
        parent_event = None
    event_divisions = None
    if parent_event:
        event_divisions = [await Event.select_one(properties={'key': k}) for k in parent_event.division_keys]
    elif event.division_keys:
        event_divisions = [await Event.select_one(properties={'key': k}) for k in event.division_keys]

    teams = await Team.at_event(event)
    num_teams = len(teams)
    await event.prep_render()
    matches_rendered = await MatchHelper.get_render_matches_event(event)
    bracket_table = BracketHelper.get_bracket(matches_rendered)
    event.alliance_selections = BracketHelper.get_alliances_from_bracket(bracket_table) if event.event_type != EventType.MEET else None
    awards = await Award.select(properties={"event_key": event.key}, extra_sql=" ORDER BY award_type, award_place")
    return html(env.get_template("event_details.html").render({
        "format_year": format_year,
        "season": year_to_season(event.year),
        "event": event,
        "parent_event": parent_event,
        "event_divisions": event_divisions,
        "matches": matches_rendered,
        "bracket_table": bracket_table,
        "teams_a": teams[:num_teams//2],
        "teams_b": teams[num_teams//2:],
        "num_teams": num_teams,
        "awards": awards,
        "AwardType": AwardType,
        "oprs": sorted([(r.team_key, r.opr) for r in event.rankings], key=lambda z: -z[1])[:15]
    }))

@app.route("/events/<season:int>")
async def events_list(request, season):
    VALID_YEARS = list(range(2018, 2006, -1))
    year = season_to_year(season)
    events = await Event.select(properties={"year": year}, extra_sql=" ORDER BY start_date, key")
    month_events = EventHelper.get_month_events(events) 
    return html(env.get_template("event_list.html").render({
        "events": events,
        "explicit_year": season,
        "selected_year": year,
        "valid_years": VALID_YEARS,
        "month_events": month_events,
        "districts": None,
        "state_prov": None,
        "valid_state_provs": {},
    }))

@app.route("/events")
async def events_list_default(request):
    return await events_list(request, 1819)

@app.route("/match/<match_key>")
async def match_details(request, match_key):
    try:
        match, red, blue = (await MatchHelper.get_match_data(where="m.key=$1", params=[match_key], use_dict=False))[0]
    except IndexError:
        abort(404)
    match_breakdown_template = "match_partials/match_breakdown/match_breakdown_default.html"
    event = await Event.select_one(properties={"key": match.event_key})
    match_render = MatchHelper.MatchRender(match, (red, blue), event)
    return html(env.get_template("match_details.html").render({
        "event": event,
        "match": match_render,
        "red": red,
        "blue": blue,
        "match_breakdown_template": match_breakdown_template
    }))
    
    
if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True, access_log=True)

