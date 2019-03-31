import logging
from models import Event, Ranking, Award, Match, MatchScore
from db.orm import orm

class ResultsPageHelper:
    """Helper methods to parse the output from FTC Live Scoring Software pages"""
    res_map = {"R": "red", "B": "blue", "T": "tie"}
    @classmethod
    def _mk_match(cls, event_key, mname, result, red_a, blue_a):
        match_code = mname.split('-')
        comp_level = match_code[0].lower() 
        mnum = int(match_code[-1])
        set_number = int(match_code[1]) if len(match_code) == 3 else None
        match = Match(event_key=event_key, comp_level=comp_level, match_number=mnum, set_number=set_number)
        scores, winner = result.split() 
        red_score, blue_score = scores.split('-')
        match.winner = cls.res_map[winner]
        match.gen_keys() 

        red = MatchScore(key=match.red_key, alliance_color="red", event_key=event_key, match_key=match.key, dqed=[], total=int(red_score), teams=[f'ftc{s.strip("*")}' for s in red_a])
        red.surrogates = [f'ftc{s.strip("*")}' for s in red_a if s.endswith('*')]

        blue = MatchScore(key=match.blue_key, alliance_color="blue", event_key=event_key, match_key=match.key, dqed=[], total=int(blue_score), teams=[f'ftc{s.strip("*")}' for s in blue_a])
        blue.surrogates = [f'ftc{s.strip("*")}' for s in blue_a if s.endswith('*')]

        return (match, red, blue)

    @classmethod
    def load_matches(cls, table, event_key):
        red_a, blue_a = None, None
        mname, result = "", ""
        matches = []
        for tr in table.find_all("tr"):
            td = [td.get_text() for td in tr.find_all("td")]
            if len(td) == 4:
                if red_a:
                    matches.append(cls._mk_match(event_key, mname, result, red_a, blue_a))
                mname = td[0]
                result = td[1]
                red_a, blue_a = [td[2]], [td[3]]
            elif len(td) == 2:
                red_a.append(td[0])
                blue_a.append(td[1])
        matches.append(cls._mk_match(event_key, mname, result, red_a, blue_a))
        return matches

    @classmethod
    def load_match_details(cls, table, event_key):
        matches = []
        for tr in table.find_all("tr"):
            td = [td.get_text() for td in tr.find_all("td")]
            if len(td) < 16:
                continue
            match, red, blue = cls._mk_match(event_key, td[0], td[1], td[2].split(), td[3].split())
            red.total, blue.total = int(td[4]), int(td[10])
            red.auto, blue.auto = int(td[5]), int(td[11])
            red.auto_bonus, blue.auto_bonus = int(td[6]), int(td[12])
            red.teleop, blue.teleop = int(td[7]), int(td[13])
            red.endgame, blue.endgame = int(td[8]), int(td[14])
            red.penalty, blue.penalty = int(td[9]), int(td[15])
            matches.append((match, red, blue))
        return matches


    @classmethod
    def load_rankings(cls, table, matches, has_hs=True):
        """has_hs=False is necessary for rly old data"""
        event_key = matches[0][0].event_key
        high_scores, wlt = cls._load_rank_data(matches) 
        ret = []
        first = True
        for tr in table.find_all("tr"):
            if first:
                first = False
                continue
            td = [td.get_text() for td in tr.find_all("td")]
            tkey = "ftc" + td[1]
            twlt = wlt[tkey]
            if not has_hs:
                r = Ranking(event_key=event_key, team_key=tkey, rank=int(td[0]), qp_rp=int(td[3]), rp_tbp=int(td[4]), 
                           high_score=high_scores.get(tkey, 0), 
                           wins=twlt[0], losses=twlt[1], ties=twlt[2], dqed=0, played=int(td[5]))
            else:
                r = Ranking(event_key=event_key, team_key=tkey, rank=int(td[0]), qp_rp=int(td[3]), rp_tbp=int(td[4]), 
                           high_score=int(td[5]),
                           wins=twlt[0], losses=twlt[1], ties=twlt[2], dqed=0, played=int(td[6]))
            ret.append(r)
        return ret

    @classmethod
    def _load_rank_data(cls, matches):
        teams = set()
        for m, red, blue in matches:
            teams.update(red.teams)
            teams.update(blue.teams)

        high_scores = {t: 0 for t in teams}
        wlt = {t: [0, 0, 0] for t in teams}
        def update_wlt(wlt, idx, teams):
            for team in teams:
                wlt[team][idx] += 1
            
        for m, red, blue in matches:
            if m.comp_level != 'q':
                continue
            for team in red.teams:
                if high_scores[team] < red.total:
                    high_scores[team] = red.total
            for team in blue.teams:
                if high_scores[team] < blue.total:
                    high_scores[team] = blue.total
            if m.winner == 'red':
                ridx, bidx = 0, 1
            elif m.winner == 'blue':
                ridx, bidx = 1, 0
            else:
                ridx, bidx = 1, 1

            update_wlt(wlt, ridx, red.teams)
            update_wlt(wlt, bidx, blue.teams)
        return high_scores, wlt
