import logging
import asyncio
from urllib.parse import urlparse
from models import Event, Match, MatchScore, Ranking
from helpers import YouTubeVideoHelper
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
            self.key = match.key
            self.video = {}
            self.youtube_videos_formatted = MatchHelper.youtube_videos_formatted(match)
    class MatchScoreRender:
        def __init__(self, match_score: MatchScore):
            self.score = match_score.total
            self.teams = match_score.teams
            self.surrogates = match_score.surrogates
            self.dqs = match_score.dqed

    @classmethod
    def youtube_videos_formatted(cls, match):
        # adapted from tba code
        if match.videos is None:
            return []
        ret = []
        for video in match.videos:
            yid = YouTubeVideoHelper.parse_id_from_url(video)
            if yid is not None:
                ret.append(yid)
        return ret

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
    async def get_render_matches_event(cls, event, team_key=None):
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
            
            #matches = await Match.fetch("SELECT * FROM matches WHERE event_key=$1 ORDER BY comp_level, set_number, match_number", event.key, conn=conn) 
            where = "m.event_key=$1"
            params = [event.key]
            if team_key:
                where += " AND ($2=ANY(red.teams) OR $2=ANY(blue.teams))"
                params.append(team_key)
            match_data = await cls.get_match_data(where=where, 
                                                  addn_sql="ORDER BY m.comp_level, m.set_number, m.match_number",
                                                  params=params, use_dict=False)
            for match, red, blue in match_data:
                if match.comp_level != 'f' and len(match.comp_level) == 1:
                    match.comp_level += 'm'
                if match.comp_level not in ret:
                    ret[match.comp_level] = []
                #scores = await MatchScore.fetch("SELECT * FROM match_scores WHERE match_key=$1", match.key, conn=conn)
                ret[match.comp_level].append(cls.MatchRender(match, (red, blue), event))
            ret['num'] = len(ret)

        return ret
    
    @classmethod
    async def get_match_data(cls, **join_kwargs):
        return (await orm.join([Match, MatchScore, MatchScore], ['m', 'red', 'blue'],
                               ["m.key=red.match_key AND red.alliance_color='red'",
                                "m.key=blue.match_key AND blue.alliance_color='blue'"],
                               **join_kwargs))
    
    @classmethod
    async def get_wlt(cls, team_key, event_key=None, year=None):
        qs = """SELECT count(*) FROM match_scores AS m1 INNER JOIN match_scores AS m2 ON 
                (m1.match_key=m2.match_key AND m1.key != m2.key 
                AND m1.total{eq}m2.total AND $1=ANY(m1.teams) {addn})"""
        args = [team_key]
        addn = ""
        if event_key:
            addn = "AND m1.event_key=$2 "
            args.append(event_key)
        if year:
            addn += "AND m1.event_key ~ $" + ("3" if event_key else "2")
            args.append(f"^{year % 100:02}{(year + 1) % 100:02}")
        ret = {}
        async with orm.pool.acquire() as conn:
            ret['wins'] = (await conn.fetchrow(qs.format(eq='>', addn=addn), *args))['count']
            ret['losses'] = (await conn.fetchrow(qs.format(eq='<', addn=addn), *args))['count']
            ret['ties'] = (await conn.fetchrow(qs.format(eq='=', addn=addn), *args))['count']
        return ret

    @classmethod
    async def generate_surrogates(cls, event_key):
        match_data = await cls.get_match_data(where="m.event_key=$1 AND m.comp_level='q'",
                                              addn_sql="ORDER BY m.match_number",
                                              params=[event_key], use_dict=False)
        if not match_data:
            return
        schedule = {}
        for match, red, blue in match_data:
            for ms in (red, blue):
                for team in ms.teams:
                    if team not in schedule:
                        schedule[team] = [ms]
                    else:
                        schedule[team].append(ms)
        played = sorted([len(s) for s in schedule.values()])
        med_played = played[len(played) // 2]
        for team, matches in schedule.items():
            if len(matches) - med_played == 0:
                continue
            else:
                m = matches[2]
                if team not in m.surrogates:
                    m.surrogates.append(team)
                await m.update()

    @classmethod
    async def generate_rankings(cls, event_key):
        match_data = await cls.get_match_data(where="m.event_key=$1", params=[event_key], use_dict=False)
        rankings = {}
        red: MatchScore
        blue: MatchScore
        match: Match
        for match, red, blue in match_data:
            for team in red.teams + blue.teams:
                if team not in rankings:
                    rankings[team] = Ranking(event_key=event_key, team_key=team, qp_rp=0, rp_tbp=0,
                                             high_score=0, wins=0, losses=0, ties=0, played=0, dqed=0)
            if match.winner == 'tie':
                for team in red.teams + blue.teams:
                    if team in red.surrogates or team in blue.surrogates:
                        continue
                    rankings[team].played += 1
                    rankings[team].ties += 1
                    rankings[team].qp_rp += 1
                    rankings[team].rp_tbp += min(red.total - red.penalty, blue.total - blue.penalty)
                continue
            elif match.winner == 'red':
                winner = red
                loser = blue
            elif match.winner == 'blue':
                winner = blue
                loser = red
            else:
                raise ValueError(f"{match.winner} is invalid value for match.winner!")
            for team in winner.teams:
                if team in winner.surrogates:
                    continue
                rankings[team].played += 1
                rankings[team].wins += 1
                rankings[team].qp_rp += 2
                rankings[team].rp_tbp += loser.total - loser.penalty
            for team in loser.teams:
                if team in loser.surrogates:
                    continue
                rankings[team].played += 1
                rankings[team].losses += 1
                rankings[team].rp_tbp += loser.total
        await asyncio.gather(*[r.upsert() for r in rankings.values()])
        await Ranking.update_ranks(event_key)
