import logging
import asyncio
from models import Event, EventType, Ranking, Award, EventParticipant
from helpers import MatchHelper, AwardHelper, OPRHelper
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

    @classmethod
    async def insert_event(cls, event, matches, rankings, awards=None, divisions=None, synch_upsert=False, tolerate_missing_finals=False):
        if divisions is None:
            divisions = []
        if not matches:
            logging.warning(f"{event.key} has no matches!")
            await event.upsert()
            if awards:
                [await a.upsert() for a in awards]
            await EventParticipant.generate(events=[event] + divisions)
            return
        m0 = [m[0] for m in matches] + [m[1] for m in matches] + [m[2] for m in matches]
        async def upsert_batch(it):
            if not it:
                return
            async with orm.pool.acquire() as conn:
                for i in it:
                    await i.upsert(conn=conn)
        await event.upsert()
        if not synch_upsert:
            await asyncio.gather(upsert_batch(m0), upsert_batch(awards), upsert_batch(rankings))
        else:
            [await upsert_batch(z) for z in [m0, awards, rankings]]

        if not rankings and not event.division_keys:
            logging.warning(f"{event.key} has no rankings, so we're generating them!")
            await MatchHelper.generate_surrogates(event.key)
            await MatchHelper.generate_rankings(event.key)

        logging.info(f"Calculating OPRs....")
        await OPRHelper.update_oprs(event.key)
        logging.info(f"Generating winning/finalist awards...")
        await AwardHelper.generate_winners_finalists(event, fail_silent=tolerate_missing_finals)
        logging.info(f"Generating EventParticipants...")
        await EventParticipant.generate(events=divisions + [event])
