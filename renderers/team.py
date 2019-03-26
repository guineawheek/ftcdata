from sanic import Sanic
from sanic.response import json, html
from sanic.exceptions import abort

from jinja2 import Environment, FileSystemLoader, ModuleLoader, select_autoescape
from template_engine import jinja2_engine
from db.orm import orm
from models import Team
from helpers import RegionHelper
import uvloop
import runtime

import asyncio
env = jinja2_engine.get_jinja_env(force_filesystemloader=True)

def format_year(year):
    return f"{year}-{(year+1)%1000:02d}"

def routes(app):
    @app.route("/team/<number:int>")
    async def teams(request, number):
        return await teams_year(request, number, None)

    @app.route("/team/<number:int>/<year:int>")
    async def teams_year(request, number, year):
        if year is None:
            team = await Team.most_recent(number=number)
            year = team.year
        else:
            team = await Team.select_one(number=number, year=year)
        if not team:
            abort(404)
        years = [r["year"] for r in await orm.pool.fetch("SELECT year FROM teams WHERE number=$1 ORDER BY year", number)]

        return html(env.get_template("team_details.html").render({
            "year": year,
            "years": years,
            "team": team,
            "format_year": format_year,
            "region_name": await RegionHelper.get_region(team)
        }))

    @app.route("/team/<number:int>/history")
    async def teams_history(request, number):
        year = await orm.pool.fetchval("SELECT max(year) FROM teams WHERE number=$1", number)
        team = await Team.select_one(number=number, year=year)
        if not team:
            abort(404)

