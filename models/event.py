from db.orm import orm
from db.types import *
__all__ = ["Event", "EventType", "PlayoffType"]
class Event(orm.Model):
    __tablename__ = "events"
    __primary_key__ = ("key",)
    key: text
    year: integer
    parent_event_key: text
    division_keys: Column("text[]")
    region: text
    league: text
    name: text
    playoff_type: integer # similar to playoff_type in tba
    field_count: integer
    advancement_slots: integer
    advances_to: text
    host_team_key: text

    event_code: text
    event_type: integer # means like championship or wahtever

    # first ES says date_start and date_end but everyone else does it the other way
    # i'm inclinde to believe that first is just a big dumbdumb
    start_date: timestamp
    end_date: timestamp
    timezone: text # lol idk?

    city: text
    state_prov: text
    country: text
    postalcode: text
    address: text
    website: text
    lat: double_precision
    lon: double_precision

    @property
    def short_name(self):
        last = self.name.split()[0]
        for part in self.name.split():
            if part.lower() == "division":
                return last
            last = part
        return self.name

class EventType:
    QUALIFIER = 1
    MEET = 2
    LEAGUE_CMP = 3
    SUPER_QUAL = 4
    REGIONAL_CMP = 5
    SUPER_REGIONAL = 6
    WORLD_CHAMPIONSHIP = 7
    FOC = 8
    SCRIMMAGE = 99
    OTHER = -1

    event_names = {
        SCRIMMAGE: "Scrimmage",
        QUALIFIER: "Qualifier",
        MEET: "Meet",
        LEAGUE_CMP: "League Championship",
        SUPER_QUAL: "Super-Qualifier",
        REGIONAL_CMP: "Championship",
        SUPER_REGIONAL: "Super-Regional Championship",
        WORLD_CHAMPIONSHIP: "World Championship",
        FOC: "Festival of Champions",
        OTHER: "Offseason Event",
    }

class PlayoffType:
    # the standard bracket
    STANDARD = 0
    BRACKET_4_ALLIANCE = 0
    # FiM did this a bunch
    BRACKET_8_ALLIANCE = 1

    # for finals divisions
    BO3_FINALS = 10
    # for FoC
    BO5_FINALS = 11
