from db.orm import orm
from models import Event, EventType


class LeagueHelper:
    @classmethod
    async def calc_rankings_before(cls, event: Event):
        meets = Event.from_record(await orm.pool.fetch("SELECT * from events WHERE event_type=$1 "
                                                 "AND region=$2 AND year=$3 AND start_date < $4"
                                                 "AND league_key=$5",
                                                 EventType.MEET, event.region, event.year,
                                                 event.start_date, event.league_key))
        team_keys = await orm.pool.fetch
