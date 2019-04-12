from db.orm import orm
from db.types import *
__all__ = ["Team"]
class Team(orm.Model):
    __tablename__ = "teams"
    __primary_key__ = ("key", "year")
    key: text
    number: integer
    year: integer
    rookie_year: integer
    name: text
    org: text
    motto: text
    home_cmp: text
    city: text
    state_prov: text
    country: text
    postalcode: text
    region: text
    normalized_location: text
    website: text
    lat: double_precision
    lon: double_precision

    @property
    def city_state_country(self):
        return f"{self.city}, {self.state_prov}, {self.country}"

    @classmethod
    async def most_recent(cls, number=None):
        return Team.from_record(await orm.pool.fetchrow(
        """SELECT * FROM teams WHERE 
           year = (SELECT max(year) FROM teams WHERE number = $1) AND number = $1""", number))
    
    @classmethod
    async def team_list(cls, k=None):
        if k == None:
            k = 1
        return await Team.fetch("SELECT * FROM teams AS a WHERE " + \
                          "year = (SELECT last_competed FROM team_meta AS b WHERE a.key = b.key) " + \
                          "AND number >= $1 AND number < $2 ORDER BY a.number", (k - 1) * 1000, k * 1000)

    @classmethod
    async def at_event(cls, event):
        from models import EventParticipant
        return [td['t'] for td in await orm.join([cls, EventParticipant], ['t', 'ep'], ['ep.team_key=t.key AND ep.event_key=$1 AND t.year=$2'], params=[event.key, event.year], addn_sql=" ORDER BY t.number")]
        """
        return await Team.fetch("SELECT * FROM rankings INNER JOIN teams ON " + \
                "(teams.key = rankings.team_key AND rankings.event_key = $1 AND teams.year = $2) ORDER BY number",
                event.key, event.year)
                """
