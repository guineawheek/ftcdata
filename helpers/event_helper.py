import logging
from models import Event, EventType, Ranking, Award, EventParticipant
from helpers import MatchHelper, AwardHelper
from db.orm import orm

class EventHelper:
    @classmethod
    def get_month_events(cls, events):
        ret = {}
        supers = []
        champs = []
        for event in events:
            if event.event_type == EventType.SUPER_REGIONAL:
                supers.append(event)
                continue
            elif event.event_type == EventType.WORLD_CHAMPIONSHIP:
                champs.append(event)
                continue
            else:
                label = event.start_date.strftime("%B")
                if label not in ret:
                    ret[label] = [event]
                else:
                    ret[label].append(event)
        if supers:
            ret["Super-Regionals"] = supers
        if champs:
            ret["FIRST Championship"] = champs
        return ret

    @classmethod
    async def get_team_events(cls, team_key, year):
        eps = await EventParticipant.select(properties={'team_key': team_key, 'year': year})
        return sorted([await cls.get_team_event(team_key, event_key=ep.event_key) for ep in eps if ep.has_awards or ep.has_matches], 
                      key=lambda te: te['event'].start_date)

    @classmethod
    async def get_team_event(cls, team_key, event_key=None, event=None):
        ret = {}
        if not (event or event_key):
            raise ValueError("must specify one of event_key, event")
        elif event_key is None:
            event_key = event.key
        elif event is None:
            event = await Event.select_one(properties={"key": event_key})
        ret['event'] = event
        ret['wlt'] = await MatchHelper.get_wlt(team_key, event_key)
        ret['ranking'] = await Ranking.select_one(properties={"event_key": event_key, "team_key": team_key})
        if ret['ranking']:
            ret['rank'] = ret['ranking'].rank
        ret['awards'] = await Award.select(properties={"event_key": event.key, "team_key": team_key}, 
                                           extra_sql=" ORDER BY award_type, award_place")
        ret['matches'] = await MatchHelper.get_render_matches_event(event, team_key)
        return ret