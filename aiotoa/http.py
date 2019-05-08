from asyncio import sleep
from urllib.parse import urlencode
import datetime
import json
import aiohttp
from async_timeout import timeout as atimeout

from .models import *

__all__ = ["AioTOAError", "TOASession"]


def endpoint(endp, query_params=None):
    def wrapper(func):
        async def new_func(self, *args, **kwargs):
            model = func.__annotations__['return']
            full_endpoint = endp.format(*args, **kwargs)
            if query_params:
                full_endpoint += "?" + urlencode({
                    key: kwargs[key] for key in query_params if key in kwargs and kwargs[key] is not None
                })

            if not str(model).startswith("typing.List"):
                # since TOA always returns lists, we must handle only doing the first
                data = await self.req(full_endpoint, List[model])
                if not len(data):
                    raise AioTOAError(f"Request to {full_endpoint} returned no data!")
                return data[0]
            else:
                return await self.req(full_endpoint, model)
        return new_func
    return wrapper


class AioTOAError(Exception):
    pass


class TOASession:
    def __init__(self, key: str, app_name: str, aiohttp_session=None, ratelimit=2, close_on_aexit=True):
        self.key = key
        self.app_name = app_name
        self.ratelimit = ratelimit
        self.last_req = datetime.datetime.now() - datetime.timedelta(seconds=ratelimit)
        self.session = aiohttp.ClientSession() if not aiohttp_session else aiohttp_session
        self.close_on_aexit = close_on_aexit

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.close_on_aexit:
            await self.session.close()

    async def close(self):
        await self.session.close()

    async def req(self, endpoint: str, model):
        if self.ratelimit:
            now = datetime.datetime.now()
            delta = (now - self.last_req).total_seconds()
            if delta < self.ratelimit:
                await sleep(self.ratelimit - delta)
            self.last_req = now

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        headers = {
            "X-Application-Origin": self.app_name,
            "X-TOA-Key": self.key,
            "Content-Type": "application/json"
        }

        async with atimeout(5) as _, self.session.get("https://theorangealliance.org/api" + endpoint, headers=headers) as response:
            # toa _still_ sometimes returns json data as text/html, making response.json() throw an exception
            # _sigh_
            data = json.loads(await response.text())
            # toa never returns data in dicts, it's always lists
            if isinstance(data, dict):
                raise AioTOAError(f"Request to {endpoint} failed with {response.status} {response.reason} (data={data})")
            return to_model(data, model)

    async def version(self) -> APIVersion:
        return await self.req("/", APIVersion)

    @endpoint("/event-types")
    async def event_types(self) -> List[EventType]:
        pass

    @endpoint("/seasons")
    async def seasons(self) -> List[Season]:
        pass

    @endpoint("/regions")
    async def regions(self) -> List[Region]:
        pass

    @endpoint("/leagues")
    async def leagues(self) -> List[League]:
        pass

    @endpoint("/streams")
    async def streams(self) -> List[EventLiveStream]:
        pass

    # /event

    @endpoint("/event", query_params=("league_key", "region_key", "season_key", "type", "includeTeamCount"))
    async def query_events(self, league_key=None, region_key=None, season_key=None, type=None, includeTeamCount=False) -> List[Event]:
        pass

    @endpoint("/event/{0}")
    async def event(self, event_key) -> Event:
        pass

    @endpoint("/event/{0}/matches")
    async def event_matches(self, event_key) -> List[Match]:
        pass

    @endpoint("/event/{0}/matches/details")
    async def event_match_details(self, event_key) -> List[MatchDetails()]:
        pass

    @endpoint("/event/{0}/matches/participants")
    async def event_match_participants(self, event_key) -> List[MatchParticipant]:
        pass

    @endpoint("/event/{0}/rankings")
    async def event_rankings(self, event_key) -> List[Ranking]:
        pass

    @endpoint("/event/{0}/streams")
    async def event_streams(self, event_key) -> List[EventLiveStream]:
        pass

    @endpoint("/event/{0}/teams")
    async def event_teams(self, event_key) -> List[TeamEventParticipant]:
        pass

    @endpoint("/event/{0}/awards")
    async def event_awards(self, event_key) -> List[AwardRecipient]:
        pass

    # /match

    @endpoint("/match/high-scores")
    async def match_high_scores(self, type="all") -> Match:  # possible values: elims, quals, all
        pass

    @endpoint("/match/{0}")
    async def match(self, match_key) -> Match:
        pass

    @endpoint("/match/{0}/matches")
    async def match_details(self, match_key) -> MatchDetails():
        pass

    @endpoint("/match/{0}/matches/details")
    async def match_participants(self, match_key) -> List[MatchParticipant]:
        pass

    # /team

    @endpoint("/team")
    async def query_teams(self, start=None, count=None) -> List[Team]:
        pass

    @endpoint("/team/{0}")
    async def team(self, team_key) -> Team:
        pass

    @endpoint("/team/{0}/events/{1}")
    async def team_events(self, team_key, season_key) -> List[EventEventParticipant]:
        pass

    @endpoint("/team/{0}/matches/{1}")
    async def team_matches(self, team_key, season_key) -> List[MatchParticipant]:
        pass

    @endpoint("/team/{0}/awards/{1}")
    async def team_awards(self, team_key, season_key) -> List[AwardRecipient]:
        pass

    @endpoint("/team/{0}/results/{1}")
    async def team_rankings(self, team_key, season_key) -> List[Ranking]:
        pass

    # /web
    @endpoint("/web/announcements")
    async def announcements(self) -> WebAnnouncement:
        pass
