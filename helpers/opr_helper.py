import logging
import numpy as np
from models import MatchScore, Ranking
from db.orm import orm

class OPRHelper:
    @classmethod
    async def update_oprs(cls, event_key):
        async with orm.pool.acquire() as conn:
            team_index = {r['team_key']: i for i, r in \
                    enumerate(await conn.fetch("SELECT team_key FROM rankings WHERE event_key=$1", event_key))}
            #"select * from match_scores where event_key='2013ohcmp' and array_length(teams, 1) = 2"
            red_scores = await MatchScore.select(conn=conn, properties={'event_key': event_key, 
                                                                        'array_length(teams, 1)': 2,
                                                                        'alliance_color': 'red'}, extra_sql=" ORDER BY match_key")
            blue_scores = await MatchScore.select(conn=conn, properties={'event_key': event_key, 
                                                                        'array_length(teams, 1)': 2,
                                                                        'alliance_color': 'blue'}, extra_sql=" ORDER BY match_key")
            match_scores = red_scores + blue_scores
            dpr_scores = blue_scores + red_scores
            match_matrix = np.zeros(shape=(len(match_scores), len(team_index)))
            for i in range(len(match_scores)):
                match_matrix[i][team_index[match_scores[i].teams[0]]] = 1
                match_matrix[i][team_index[match_scores[i].teams[1]]] = 1
            opr_scores = np.array([m.total for m in match_scores])
            dpr_scores = np.array([m.total for m in dpr_scores])
            ccwm_scores = opr_scores - dpr_scores
            opr = np.linalg.lstsq(match_matrix, opr_scores, rcond=None)[0]
            dpr = np.linalg.lstsq(match_matrix, dpr_scores, rcond=None)[0]
            ccwm = np.linalg.lstsq(match_matrix, ccwm_scores, rcond=None)[0]
            for team_key, i in team_index.items():
                rank = await Ranking.select_one(conn=conn, properties={'event_key': event_key, 'team_key': team_key})
                rank.opr = opr[i]
                rank.dpr = dpr[i]
                rank.ccwm = ccwm[i]
                await rank.update(keys=("opr", "dpr", "ccwm"), conn=conn)
