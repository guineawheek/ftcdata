from sanic import Sanic
import sanic.response
from sanic.response import json, html
from jinja2 import Environment, FileSystemLoader, ModuleLoader, select_autoescape
from template_engine import jinja2_engine
from db.orm import orm
from models import Team
import runtime

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

@app.route("/<name>")
async def template(request, name):
    if not name.endswith(".html"):
        name += ".html"
    return html(env.get_template(name).render({}))

@app.route("/team/<number>")
async def teams(request, number):
    return html(env.get_template("teams.html").render({}))

if __name__ == "__main__":
    asyncio.run_until_complete(runtime.setup_orm(orm))
    app.run(host="0.0.0.0", port=8000, debug=True)

