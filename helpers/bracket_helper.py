class BracketHelper:
    @classmethod
    def get_bracket(cls, matches_r):
        ret = {}
        # schema: 
        # bracket.sf.1
        #.winning_alliance, .red_alliance, blue_alliance
        for match_level in matches_r.keys():
            if not match_level.endswith("f"):
                continue
            ret_ml = {}
            sets = {}
            for match in matches_r[match_level]:
                set_n = match.set_number or 1
                if set_n not in sets:
                    sets[set_n] = [match]
                else:
                    sets[set_n].append(match)
            for set_number, matches in sets.items():
                ret_ml[int(set_number)] = {
                        "winning_alliance": matches[-1].winning_alliance,
                        "red_alliance": matches[-1].alliances['red'].teams,
                        "blue_alliance": matches[-1].alliances['blue'].teams,
                }
            ret[match_level] = ret_ml
        return ret
    
    @classmethod
    def get_alliances_from_bracket(cls, bracket_table):
        level = 'ef'
        N = 16
        for level in ('ef', 'qf', 'sf', 'f'):
            if level in bracket_table:
                break
            N //= 2
        mlevel = bracket_table[level] 
        ret = [dict() for i in range(N)]
        for set_number, set_info in mlevel.items():
            s = set_number - 1
            ret[s]['picks'] = set_info['red_alliance']
            ret[-(s + 1)]['picks'] = set_info['blue_alliance']
        return ret
