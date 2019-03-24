from db.orm import orm
from db.types import *
__all__ = ["Match", "MatchScore"]
class Match(orm.Model):
    __tablename__ = "matches"
    __primary_key__ = ("key",)
    key: text
    event_key: text # can be a division key
    comp_level: text # quals/elims basically
    match_number: integer
    set_number: integer
    red: text
    blue: text
    winner: text
    videos: Column("text[]")
    def gen_keys(self):
        self.key = f"{self.event_key}_{self.comp_level}{self.set_number if self.set_number else ''}m{self.match_number}"
        self.red = self.key + "_red"
        self.blue = self.key + "_blue"

class MatchScore(orm.Model):
    __tablename__ = "match_scores"
    __primary_key__ = ("key",)
    key: text
    event_key: text
    alliance_color: text
    teams: Column("text[]")
    surrogates: Column("text[]")
    dqed: boolean
    total: integer
    auto: integer
    auto_bonus: integer # typically not used in modern games
    teleop: integer
    endgame: integer
    penalty: integer
    breakdown: Column("json")

