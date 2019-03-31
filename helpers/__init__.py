from .location_helper import LocationHelper
from .champ_split_helper import ChampSplitHelper
from .nominatim_helper import NominatimHelper
from .region_helper import RegionHelper
from .opr_helper import OPRHelper
from .youtube_video_helper import YouTubeVideoHelper
from .match_helper import MatchHelper
from .bracket_helper import BracketHelper
from .award_helper import AwardHelper
from .event_helper import EventHelper
from .results_page_helper import ResultsPageHelper
def format_year(year):
    return f"{year}-{(year+1)%1000:02d}"

def format_season(season):
    return format_year(season_to_year(season))

def year_to_season(year):
    return f"{year % 100:02}{(year + 1) % 100:02}"

def season_to_year(season):
    season = int(season)
    return (season % 100) - 1 + 2000
