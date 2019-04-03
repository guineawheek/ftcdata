import logging
from models import Award, AwardType, EventType
from helpers import MatchHelper
from db.orm import orm

class AwardHelper:
    @classmethod
    async def generate_winners_finalists(cls, event, fail_silent=False):
        finals = (await MatchHelper.get_match_data(
                         where="m.comp_level='f' AND m.event_key=$1", 
                         addn_sql="ORDER BY m.match_number",
                         params=(event.key,)))
        #print(finals)
        if len(finals) == 0:
            if event.event_type == EventType.MEET:
                return
            logging.warning(f"[award_helper.py]: {event.key} doesn't have finals matches wtf")
            if not fail_silent:
                raise Exception(f"query failed on {event.key} oops")
            return
        last_finals = finals[-1]
        if last_finals['m'].winner == 'red':
            winning_alliance = last_finals['red'].teams
            finalist_alliance = last_finals['blue'].teams
        else:
            winning_alliance = last_finals['blue'].teams
            finalist_alliance = last_finals['red'].teams
        awards = []
        for idx, team in enumerate(winning_alliance, 1):
            a = Award(name=event.award_prefix + "Winner",
                      award_type=AwardType.WINNING_ALLIANCE,
                      award_place=idx,
                      event_key=event.key,
                      team_key=team)
            awards.append(a)

        for idx, team in enumerate(finalist_alliance, 1):
            a = Award(name=event.award_prefix + "Finalist",
                      award_type=AwardType.FINALIST_ALLIANCE,
                      award_place=idx,
                      event_key=event.key,
                      team_key=team)
            awards.append(a)
        async with orm.pool.acquire() as conn:
            for a in awards:
                await a.upsert(conn=conn)

    @classmethod
    async def sorted_awards(cls, awards):
        return sorted(awards, key=lambda a: a.award_type * 100 + a.award_place)

