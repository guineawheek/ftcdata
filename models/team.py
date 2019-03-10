from db.orm import orm
from db.types import *
class Team(orm.Model):
    __tablename__ = "teams"
    __primary_key__ = ("key", "year")
    key: varchar(20)
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

