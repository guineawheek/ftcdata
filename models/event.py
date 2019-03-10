from db.orm import orm
from db.types import *
"""
from first reg:
date_end: "2019-04-20T00:00:00"
date_start: "2019-04-16T00:00:00"
event_address1: "1001 Avenida De Las Americas"
event_city: "Houston"
event_code: "FTCCMP1"
event_country: "USA"
event_fee_base: 2000
event_fee_currency: "USD"
event_name: "FIRST Championship- Houston- World Championship- FIRST Tech Challenge"
event_name_analyzed: "FIRST Championship- Houston- World Championship- FIRST Tech Challenge"
event_name_sort: "FIRST Championship- Houston- World Championship- FIRST Tech Challenge"
event_postalcode: "77010"
event_season: 2018
event_stateprov: "TX"
event_subtype: "World Championship"
event_subtype_moniker: "World Championship"
event_type: "FTC"
event_venue: "George R. Brown Convention Center"
event_venue_analyzed: "George R. Brown Convention Center"
event_venue_sort: "George R. Brown Convention Center"
"""
class Event(orm.Model):
    __tablename__ = "events"
    __primary_key__ = ("key",)
    key: varchar(32)
    year: integer
    region: text
    league: text
    name: text
    comp_format: text
    field_count: integer
    advancement_slots: integer
    advances_to: varchar(32)
    host_team_key: varchar(20)

    event_code: text
    event_type: text # means like championship or wahtever
    event_fee_base: integer
    event_fee_currency: text

    date_start: timestamp
    date_end: timestamp
    timezone: text # lol idk?

    city: text
    state_prov: text
    country: text
    postalcode: text
    address: text
    website: text
    lat: double_precision
    lon: double_precision
