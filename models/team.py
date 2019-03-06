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

