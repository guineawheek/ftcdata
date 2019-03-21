import pycountry
import functools
class LocationHelper:

    _remap = {
        "South Korea": "Korea, Republic Of",
        "Chinese Taipei": "Taiwan",
        "Russia": "Russian Federation",
        "Iran": "Iran, Islamic Republic Of",
    }

    @classmethod
    @functools.lru_cache(maxsize=256)
    def unabbrev_state_prov(cls, country, state_prov):
        # these are military overseas addresses
        # there are ways to resolve this to correct championships
        # i'm just too lazy rn
        if country == "USA" and state_prov == "AE":
            return "Armed Forces Europe"
        if country == "USA" and state_prov == "AP":
            return "Armed Forces Pacific"
        
        # fix some pedantic issues
        if country in cls._remap:
            country = cls._remap[country]

        # fix the one cayman islands case
        elif country == "Cayman Islands":
            # idk why the state_prov field is filled for this one
            return ""
        # and the south africa case
        if country == "South Africa" and state_prov == "GP":
            return "Gauteng"
        elif country == "Mali" and state_prov == "BKO":
            return "Bamako"
        # some countries don't have divisions ig
        if not state_prov.strip():
            return ''
        # like 2 entries are already expanded for some reason
        # division codes won't be above 3 characters
        if len(state_prov) > 3:
            return state_prov
        if country == "USA" and state_prov == "22":
            return state_prov
        cc = pycountry.countries.lookup(country)
        if cc is None:
            # country lookup failed whoops
            return state_prov
        st = pycountry.subdivisions.lookup(cc.alpha_2 + "-" + state_prov)
        return st.name if st else state_prov

    @classmethod
    def unabbrev_state_prov_team(cls, team):
        return cls.unabbrev_state_prov(team.country, team.state_prov)

    @classmethod
    def abbrev_state_prov(cls, country, state_prov):
        pass

