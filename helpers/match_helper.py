import logging
import numpy as np
from models import Event, Ranking, Match, MatchScore
from db.orm import orm

class MatchHelper:
    class MatchRender:
        def __init__(self, match: Match, scores, event: Event):
            self.year = event.year
            self.has_video = bool(match.videos)
            # url safety????
            self.details_url = "/match/" + match.key
            self.event_key = event.key
            self.verbose_name = MatchHelper.verbose_name(match)
            #TODO: do
            self.score_breakdown = {}
            self.alliances = {}
            for match_score in scores:
                self.alliances[match_score.alliance_color] = MatchHelper.MatchScoreRender(match_score)
            self.winning_alliance = match.winner
            self.set_number = match.set_number
            self.match_number = match.match_number
            self.has_been_played = True
    class MatchScoreRender:
        def __init__(self, match_score: MatchScore):
            self.score = match_score.total
            self.teams = match_score.teams
            self.surrogates = match_score.surrogates
            self.dqs = match_score.dqed

    @classmethod
    def verbose_name(cls, match):
        match_type = {
                'p': 'Practice',
                'pm': 'Practice',
                'q': 'Quals',
                'qm': 'Quals',
                'qf': 'Quarters',
                'sf': 'Semis',
                'f': 'Finals',
        }.get(match.comp_level, '')
        if match_type not in ("Practice", "Quals", "Finals"):
            match_label = "Match "
        else:
            match_label = ""
        if match.set_number:
            set_label = f"{match.set_number} "
        else:
            set_label = ""
        return f"{match_type} {set_label}{match_label}{match.match_number}"
        
    @classmethod
    async def get_render_matches_event(cls, event):
        ret = {}
        async with orm.pool.acquire() as conn:
            #TODO: get qm, sf, f, etc.
            # on the lowest level:
            # match.key_name??
            # match.year....
            # match.has_video, match.details_url
            # match.event_key
            # match.verbose_name????
            # match.score_breakdown.get(color).props
            # match.alliances.get(alliance_color).score (int)
            #                                    .teams (list)
            #                                    .surrogates (list)
            #                                    .dqs (list)
            # match.winning_alliance

            # ORDER BY should already sort within its own category.
            
            matches = await Match.fetch("SELECT * FROM matches WHERE event_key=$1 ORDER BY comp_level, set_number, match_number", event.key, conn=conn) 
            
            ret['num'] = len(ret)
            for match in matches:
                if match.comp_level != 'f' and len(match.comp_level) == 1:
                    match.comp_level += 'm'
                if match.comp_level not in ret:
                    ret[match.comp_level] = []
                scores = await MatchScore.fetch("SELECT * FROM match_scores WHERE match_key=$1", match.key, conn=conn)
                ret[match.comp_level].append(cls.MatchRender(match, scores, event))

        return ret
                
