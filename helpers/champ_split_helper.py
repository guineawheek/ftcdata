# edited from 
import logging


class ChampSplitHelper(object):
    """
    http://www.firstinspires.org/sites/default/files/uploads/championship/first-championship-maps-2017-2018.pdf
    """
    STL = 'St. Louis'
    HOU = 'Houston'
    DET = 'Detroit'

    YELLOW = {2016: HOU, 2017: HOU}
    BLUE = {2016: STL, 2017: DET}

    LOCATION_CHAMP_MAP = {
        'USA': {
            'Washington': HOU,
            'Oregon': HOU,
            'California': HOU,
            'Nevada': HOU,
            'Idaho': HOU,
            'Montana': HOU,
            'Wyoming': HOU,
            'Colorado': HOU,
            'Utah': HOU,
            'Arizona': HOU,
            'New Mexico': HOU,
            'Texas': HOU,
            'Oklahoma': HOU,
            'Arkansas': HOU,
            'Louisiana': HOU,
            'Mississippi': HOU,
            'Tennessee': HOU,
            'Alabama': HOU,
            'Georgia': HOU,
            'North Carolina': HOU,
            'South Carolina': HOU,
            'Florida': HOU,
            'Alaska': HOU,
            'Hawaii': HOU,
            'Armed Forces Pacific': HOU
        },
        'Canada': {
            'Yukon': HOU,
            'Northwest Territories': HOU,
            'British Columbia': HOU,
            'Alberta': HOU,
            'Saskatchewan': HOU,
        },
        'Brazil': YELLOW,
        'Ecuador': YELLOW,
        'Israel': YELLOW,
        'Australia': YELLOW,
        'Singapore': YELLOW,
        'Chile': YELLOW,
        'China': YELLOW,
        'Dominican Republic': YELLOW,
        'Philippines': YELLOW,
        'Turkey': YELLOW,
        'Mexico': YELLOW,
        'United Arab Emirates': YELLOW,
        'India': YELLOW,
        'Colombia': YELLOW,
        'Malaysia': YELLOW,
        'Ethiopia': YELLOW,
        'Morocco': YELLOW,
        'Paraguay': YELLOW,
        # begin added teams
        'New Zealand': YELLOW,
        'Egypt': YELLOW,
        'Zimbabwe': YELLOW,
        'Nigeria': YELLOW,
        'Tonga': YELLOW,
        'Indonesia': YELLOW,
        'Cayman Islands': YELLOW,
        'Lebanon': YELLOW,
        'Qatar': YELLOW,
        'Mali': YELLOW,
        'South Africa': YELLOW,
        'Cyprus': YELLOW, # competes in Israel
        'Costa Rica': YELLOW,
        'Uganda': YELLOW,
        'Tunisia': YELLOW,
        'Saudi Arabia': YELLOW,
        'Bahrain': YELLOW,
        'Jamaica': BLUE, # despite being yellow, they always seem to go detroit?
        'Romania': BLUE,
        'Ukraine': BLUE,
        'Serbia': BLUE,
        'Slovenia': BLUE,
        'South Korea': BLUE,
        'Russia': BLUE,
        'Iran': BLUE,
        'Thailand': BLUE,
        'Portugal': BLUE,
        'Bulgaria': BLUE,
        'Belgium': BLUE,
        'Latvia': BLUE,
        'Austria': BLUE,
        'Albania': BLUE,
        'Norway': BLUE,
        # end added teams
        'Kazakhstan': BLUE,
        'Germany': BLUE,
        'Spain': BLUE,
        'Netherlands': BLUE,
        'Denmark': BLUE,
        'Pakistan': BLUE,
        'Poland': BLUE,
        'United Kingdom': BLUE,
        'Japan': BLUE,
        'Taiwan': BLUE,
        'Chinese Taipei': BLUE,
        'Bosnia-Herzegovina': BLUE,
        'Kingdom': BLUE,
        'Czech Republic': BLUE,
        'France': BLUE,
        'Switzerland': BLUE,
        'Vietnam': BLUE,
        'Croatia': BLUE,
        'Sweden': BLUE,
        'Italy': BLUE,
        'Greece': BLUE,
    }

    @classmethod
    def get_champ(cls, team):
        if team.country in cls.LOCATION_CHAMP_MAP:
            if team.country in {'USA', 'Canada'}:
                if team.state_prov in cls.LOCATION_CHAMP_MAP[team.country]:
                    champ = cls.LOCATION_CHAMP_MAP[team.country][team.state_prov]
                    return {2016: champ, 2017: champ}
                elif team.state_prov in {'Kansas', 'Missouri'}:
                    return {2016: cls.STL, 2017: cls.HOU}
                elif team.state_prov.startswith("Armed Forces"):
                    # team.region is usually their actual country sooo
                    return cls.LOCATION_CHAMP_MAP[team.region]
                else:
                    # All other unlabled states and provinces in US and CA are STL/DET
                    return {2016: cls.STL, 2017: cls.DET}
            else:
                # Non US/CA other countries
                return cls.LOCATION_CHAMP_MAP[team.country]
        else:
            if team.country is not None:
                logging.warning("[champ_split_helper.py] Unknown country: {}".format(team.country))
            return None
