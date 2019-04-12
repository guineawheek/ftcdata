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
        qs = f"""UPDATE {cls.table_name()} SET rank=sq.rank FROM 
            (SELECT team_key, ROW_NUMBER() OVER 
                (ORDER BY qp_rp DESC, rp_tbp DESC, high_score DESC) AS rank 
                    FROM {cls.table_name()} WHERE event_key=$1) 
        AS sq WHERE event_key=$1 AND {cls.table_name()}.team_key=sq.team_key;"""
        return await cls.fetchrow(qs, event_key, conn=conn)

    def __eq__(self, other):
        return self.qp_rp == other.qp_rp and self.rp_tbp == other.rp_tbp and \
               self.high_score == other.high_score

    def __gt__(self, other):
        return not self.__lt__(other)

    def __lt__(self, other):
        if self.__eq__(other):
            return False
        if self.qp_rp < other.qp_rp:
            return True
        elif self.qp_rp == other.qp_rp:
            if self.rp_tbp < other.rp_tbp:
                return True
            elif self.rp_tbp == other.rp_tbp and self.high_score < other.high_score:
                return True
        return False
