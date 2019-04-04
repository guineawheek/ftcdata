from db.orm import orm
from db.types import *
from models.ranking import Ranking
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
    league_key: text

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
    venue: text
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

    @property
    def season(self):
        return f"{self.year % 100:02}{(self.year + 1) % 100:02}"

    @property
    def award_prefix(self):
        ret = ""
        if self.event_type in [EventType.REGIONAL_CMP, EventType.SUPER_REGIONAL, EventType.WORLD_CHAMPIONSHIP, EventType.FOC]:
            ret += EventType.event_names[self.event_type] + " "
        else:
            ret += "Event "
        if self.parent_event_key:
            ret += "Division "
        return ret
    
    @property
    def location(self):
        return ", ".join(c for c in (self.city, self.state_prov, self.country) if c)

    @property
    def city_state_country(self):
        return self.location

    async def prep_render(self):
        # TODO: move this into a helper LOL
        labels = ["Rank", "Team", "Qual Points", "Rank Points", "High Score", "Record (W-L-T)", "DQ", 
                  "Played", "Qual Points/Match*"]
        if self.year > 2017:
            labels[2] = "Rank Points"
            labels[3] = "Tiebreaker Points"
            labels[-1] = "Rank Points/Match*"
        self.rankings = await Ranking.fetch("SELECT * from rankings WHERE event_key=$1 ORDER BY rank", self.key)
        self.rankings_table = [labels] + \
                [(r.rank, r.team_key, r.qp_rp, r.rp_tbp, r.high_score, f"{r.wins}-{r.losses}-{r.ties}", 0, r.played, round(r.qp_rp / r.played, 2)) for r in self.rankings if r.played]
    @classmethod
    async def purge(cls, event_key):
        lines = """
        DELETE FROM awards WHERE event_key=$1;
        DELETE FROM rankings WHERE event_key=$1;
        DELETE FROM event_participants WHERE event_key=$1;
        DELETE FROM matches WHERE event_key=$1;
        DELETE FROM match_scores WHERE event_key=$1;
        DELETE FROM events WHERE key=$1;
        """
        for a in lines.strip().split("\n"):
            await orm.pool.fetch(a, event_key)

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
