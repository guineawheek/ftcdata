from db.orm import orm
from db.types import *
__all__ = ["Ranking"]
class Ranking(orm.Model):
    __tablename__ = "rankings"
    __primary_key__ = ("event_key", "team_key")
    event_key: text # can be a division key
    team_key: text # quals/elims basically
    rank: integer
    qp_rp: integer # called "rp" for 1819+
    rp_tbp: integer # called "tbp" for 1819+
    high_score: integer
    wins: integer
    losses: integer
    ties: integer
    played: integer
    dqed: integer
    opr: double_precision
    dpr: double_precision
    ccwm: double_precision
    
    @classmethod
    async def update_ranks(cls, event_key, conn=None):
        qs = """UPDATE rankings SET rank=sq.rank FROM 
            (SELECT team_key, ROW_NUMBER() OVER 
                (ORDER BY qp_rp DESC, rp_tbp DESC, high_score DESC) AS rank 
                    FROM rankings WHERE event_key=$1) 
        AS sq WHERE event_key=$1 AND rankings.team_key=sq.team_key;"""
        return await cls.fetchrow(qs, event_key, conn=conn)
