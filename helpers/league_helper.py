from db.orm import orm
from helpers import MatchHelper
from models import Event, EventType, Ranking
import heapq

def enqueue(item, heap, max_size=10):
    if len(heap) == max_size and heap[0] < item:
        # remove smallest for being small
        heapq.heappop(heap)
    heapq.heappush(heap, item)

class LeagueHelper:
    class MatchItem:
        qp_rp: int
        rp_tbp: int
        score: int
        match_tuple: tuple

        def __init__(self, **stuff):
            self.__dict__.update(stuff)

        def __eq__(self, other):
            return self.qp_rp == other.qp_rp and self.rp_tbp == other.rp_tbp and self.score == other.score

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
                elif self.rp_tbp == other.rp_tbp and self.score < other.score:
                    return True
            return False

        def __repr__(self):
            return f"MatchItem(qp_rp={self.qp_rp}, rp_tbp={self.rp_tbp}, score={self.score})"

    @classmethod
    async def calc_rankings_before(cls, event: Event, teams_at_event=False):
        meets = await Event.fetch("SELECT * from events WHERE event_type=$1 "
                                  "AND (region=$2 OR league_key=$5) AND year=$3 AND start_date < $4",
                                  EventType.MEET, event.region, event.year,
                                  event.start_date, event.league_key)
        # query meets
        # find all the teams in the meets
        # find their best matches
        meet_keys = [m.key for m in meets]
        if teams_at_event:
            mk = [event.key]
        else:
            mk = meet_keys
        team_keys = {r['team_key'] for r in await orm.pool.fetch("SELECT DISTINCT team_key FROM "
                                                                 "event_participants WHERE "
                                                                 "event_key=ANY($1)", meet_keys)}

        matches = await MatchHelper.get_match_data(where="m.event_key=ANY($1) AND m.comp_level='q'",
                                                   params=[meet_keys], use_dict=False)
        return await cls.calc_rankings(matches, team_keys)

    @classmethod
    async def calc_rankings(cls, matches, team_keys: set):
        # the correct way to do this would be to use a minPQ
        best_ten = {k: [] for k in team_keys}

        for m, red, blue in matches:
            if team_keys.isdisjoint(red.teams) and team_keys.isdisjoint(blue.teams):
                continue
            if m.winner == "tie":
                mi = cls.MatchItem(qp_rp=1, score=red.total, match_tuple=(m, red, blue),
                                   rp_tbp=min(red.total - red.penalty, blue.total - blue.penalty))
                for team in red.teams + blue.teams:
                    if team in red.surrogates or team in blue.surrogates:
                        continue
                    if team in team_keys:
                        enqueue(mi, best_ten[team])
                continue
            elif m.winner == "red":
                winner, loser = red, blue
            elif m.winner == "blue":
                winner, loser = blue, red
            else:
                raise ValueError(f"match.winner for {m.key} is not in {{'red', 'blue', 'tie'}}")

            for team in winner.teams:
                if team in winner.surrogates:
                    continue
                mi = cls.MatchItem(qp_rp=2, score=winner.total, match_tuple=(m, red, blue),
                                   rp_tbp=loser.total - loser.penalty)
                print(team, repr(mi))
                if team in team_keys:
                    enqueue(mi, best_ten[team])

            for team in loser.teams:
                if team in loser.surrogates:
                    continue
                mi = cls.MatchItem(qp_rp=0, score=loser.total, match_tuple=(m, red, blue),
                                   rp_tbp=loser.total - loser.penalty)
                print(team, repr(mi))
                if team in team_keys:
                    enqueue(mi, best_ten[team])
        ret = []
        import pprint
        pprint.pprint(best_ten)
        for team, match_item in best_ten.items():
            ret.append(Ranking(
                team_key=team,
                qp_rp=sum(a.qp_rp for a in match_item),
                rp_tbp=sum(a.rp_tbp for a in match_item),
                high_score=max(a.score for a in match_item),
                wins=len([2 for a in match_item if a.qp_rp == 2]),
                losses=len([0 for a in match_item if a.qp_rp == 0]),
                ties=len([0 for a in match_item if a.qp_rp == 1]),
                played=len(match_item),
                dqed=0,
            ))
        return ret
