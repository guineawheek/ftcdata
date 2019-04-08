from db.orm import orm
from models import Event, EventType


class LeagueHelper:
    @classmethod
    async def calc_rankings_before(cls, event: Event, teams_at_event=False):
        meets = Event.from_record(await orm.pool.fetch("SELECT * from events WHERE event_type=$1 "
                                                 "AND region=$2 AND year=$3 AND start_date < $4"
                                                 "AND league_key=$5",
                                                 EventType.MEET, event.region, event.year,
                                                 event.start_date, event.league_key))
        # query meets
        # find all the teams in the meets
        # find their best matches
        meet_keys = [m.key for m in meets]
        if teams_at_event:
            mk = [event.key]
        else:
            mk = meet_keys
        team_keys = {r['team_key'] for r in await orm.pool.fetch("SELECT DISTINCT team_key FROM "
                                                                 "event_participants WHERE "
                                                                 "event_key=ANY($1)", meet_keys)}
        pass

    @classmethod
    async def calc_rankings(cls, matches):
        pass
