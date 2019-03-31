from db.orm import orm
from db.types import *
from models import Event, Ranking, Award, MatchScore
import asyncio
import logging
__all__ = ["EventParticipant"]
class EventParticipant(orm.Model):
    __tablename__ = "event_participants"
    __primary_key__ = ("event_key", "team_key")
    event_key: text # can be a division key
    team_key: text # quals/elims basically
    year: integer
    has_matches: boolean
    has_awards: boolean

    @classmethod
    async def generate(cls, year=None, events=None):
        if events == None and year is not None:
            events = await Event.select(properties={"year": year})
        elif events == None and year == None:
            raise ValueError("year= needs to be specified without events!")
        await cls._generate(events, year=year)
    @classmethod
    async def _generate(cls, events, year=None):
        if not year:
            year = events[0].year
        ep_map = {}
        async with orm.pool.acquire() as conn:
            for event in events:
                for ranking in await Ranking.select(properties={"event_key": event.key}, conn=conn):
                    ep_map[(ranking.team_key, event.key)] = cls(event_key=event.key, team_key=ranking.team_key,
                                                                year=year, has_matches=True, has_awards=False)
                    # teams are _technically_ in the awards/finals division
                    if event.parent_event_key and (ranking.team_key, event.parent_event_key) not in ep_map:
                        cls.cls = cls(event_key=event.parent_event_key, team_key=ranking.team_key, year=year,
                                      has_matches=False, has_awards=False)
                        ep_map[(ranking.team_key, event.parent_event_key)] = cls.cls
            for event in events:
                for award in await Award.select(properties={"event_key": event.key}, conn=conn):
                    if (award.team_key, event.key) in ep_map:
                        ep_map[(award.team_key, event.key)].has_awards = True
                    elif not event.division_keys:
                        logging.warning(f"[EventParticipant] {award.team_key} got an award at {event.key} without competing lol")

            for match_score, event in await orm.join([MatchScore, Event], ['m', 'e'],
                                               ["m.event_key=e.key AND array_length(e.division_keys, 1) > 0 AND year=$1"], params=[year],
                                               use_dict=False):
                for team in match_score.teams:
                    ep_map[(team, event.key)].has_matches=True
        await asyncio.gather(*[ep.upsert() for ep in ep_map.values()])
