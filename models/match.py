from db.orm import orm
from db.types import *
class Match(orm.Model):
    __tablename__ = "matches"
    __primary_key__ = ("key",)
    key: varchar(32)
    event_key: varchar(32)
    comp_level: text
    match_number: integer
    set_number: integer
    red: varchar(32)
    blue: varchar(32)
    winner: text
    videos: Column("varchar(32)[]")

class MatchScore(orm.Model):
    __tablename__ = "match_scores"
    __primary_key__ = ("key",)
    key: varchar(32)
    event_key: varchar(32)
    teams: Column("varchar(20)[]")
    total: integer
    auto: integer
    auto_bonus: integer # typically not used in modern games
    teleop: integer
    endgame: integer
    penalty: integer
    breakdown: Column("json")
