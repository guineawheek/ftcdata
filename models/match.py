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
    red_key: text
    blue_key: text
    winner: text
    videos: Column("text[]")
    def gen_keys(self):
        self.key = f"{self.event_key}_{self.comp_level}{self.set_number if self.set_number else ''}m{self.match_number}"
        self.red_key = self.key + "_red"
        self.blue_key = self.key + "_blue"
    def __repr__(self):
        if self.set_number:
            lsm = f"{self.comp_level}-{self.match_number}-{self.set_number}"
        else:
            lsm = f"{self.comp_level}-{self.match_number}"
        return f"{self.key} {lsm} {self.winner}"

class MatchScore(orm.Model):
    __tablename__ = "match_scores"
    __primary_key__ = ("key",)
    key: text
    event_key: text
    match_key: text
    alliance_color: text
    teams: Column("text[]")
    surrogates: Column("text[]")
    dqed: Column("text[]")
    total: integer
    auto: integer
    auto_bonus: integer # typically not used in modern games
    teleop: integer
    endgame: integer
    penalty: integer
    breakdown: Column("json")

    def __repr__(self):
        return f"{self.alliance_color} {self.total} [{', '.join(self.teams)}]"
