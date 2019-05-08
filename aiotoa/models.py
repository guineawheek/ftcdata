import datetime
from typing import Dict, Tuple, List, Union, Any


class Converter:
    repr_str = ""

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__}" + self.repr_str.format(s=self) + ">"


class Timestamp(Converter):
    def __init__(self, fmt="%Y-%m-%dT%H:%M:%S.%fZ"):
        self.fmt = fmt

    def __call__(self, value) -> datetime.datetime:
        if self.fmt != "unix":
            return datetime.datetime.strptime(value, self.fmt)
        else:
            return datetime.datetime.fromtimestamp(value)


class Model(Converter):
    __prefix__ = ""

    def __init__(self, data):

        cutoff = len(self.__prefix__)
        # self._data = data

        # base classes annotations should be incorporated into the list of fields
        fields = dict(self.__annotations__)
        for base in self.__class__.__bases__:
            if hasattr(base, "__annotations__"):
                fields.update(base.__annotations__)

        for field_name, field_type in fields.items():
            try:
                if field_name[cutoff:] in data:
                    setattr(self, field_name, to_model(data[field_name[cutoff:]], field_type))
                else:
                    setattr(self, field_name, None)
            except TypeError:
                raise

    def __contains__(self, item):
        return item in self.__annotations__

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return getattr(self, key)


# models go here
class APIVersion(Model):
    version: str


class WebAnnouncement(Model):
    announcement_key: str
    title: str
    publish_date: str
    is_active: bool
    text: str
    author: str


class EventType(Model):
    event_type_key: str
    description: str


class Season(Model):
    season_key: str
    description: str
    is_active: bool


class Region(Model):
    region_key: str
    description: str


class League(Model):
    league_key: str
    region_key: str
    description: str


class EventLiveStream(Model):
    stream_key: str
    event_key: str
    channel_name: str
    stream_name: str
    stream_type: int
    is_active: bool
    url: str
    start_datetime: Timestamp()
    end_datetime: Timestamp()
    channel_url: str


class Event(Model):
    event_key: str
    season_key: str
    region_key: str
    league_key: str
    event_code: str
    event_type_key: str
    event_region_number: str
    division_key: int
    division_name: str
    event_name: str
    start_date: Timestamp()
    end_date: Timestamp()
    week_key: str
    city: str
    state_prov: str
    country: str
    venue: str
    website: str
    time_zone: str
    is_active: bool
    is_public: bool
    active_tournament_level: int
    alliance_count: int
    field_count: int
    advance_spots: str
    advance_event: str
    team_count: int


class MatchParticipant(Model):
    match_participant_key: str
    match_key: str
    team_key: str
    station: int
    station_status: int
    ref_status: int


class Match(Model):
    match_key: str
    event_key: str
    tournament_level: int
    scheduled_time: Timestamp("%Y-%m-%d %H:%M:%S")
    match_name: str
    play_number: int
    field_number: int
    prestart_time: Timestamp("%Y-%m-%d %H:%M:%S")
    prestart_count: int
    cycle_time: Timestamp("%H:%M:%S.%f")
    red_score: int
    blue_score: int
    red_penalty: int
    blue_penalty: int
    red_auto_score: int
    blue_auto_score: int
    red_tele_score: int
    blue_tele_score: int
    red_end_score: int
    blue_end_score: int
    video_url: str
    participants: List[MatchParticipant]


class BaseMatchDetails(Model):
    def __init__(self, data):
        self._data = data
        super().__init__(data)

    match_detail_key: str
    match_key: str
    red_min_pen: int
    blue_min_pen: int
    red_maj_pen: int
    blue_maj_pen: int


class VelocityVortexMatchDetails(BaseMatchDetails):
    red_auto_beacons: int
    red_auto_cap: bool
    red_auto_part_cen: int
    red_auto_part_cor: int
    red_auto_robot_1: int
    red_auto_robot_2: int
    red_tele_beacons: int
    red_tele_part_cen: int
    red_tele_part_cor: int
    red_tele_cap: int
    blue_auto_beacons: int
    blue_auto_cap: bool
    blue_auto_part_cen: int
    blue_auto_part_cor: int
    blue_auto_robot_1: int
    blue_auto_robot_2: int
    blue_tele_beacons: int
    blue_tele_part_cen: int
    blue_tele_part_cor: int
    blue_tele_cap: int


class RelicRecoveryMatchDetails(BaseMatchDetails):
    red_auto_jewels: int
    red_auto_glyphs: int
    red_auto_keys: int
    red_auto_parks: int
    red_tele_glyphs: int
    red_tele_rows: int
    red_tele_cols: int
    red_tele_cyphers: int
    red_end_relic_1: int
    red_end_relic_2: int
    red_end_relic_3: int
    red_end_relic_standing: int
    red_end_robot_balances: int
    blue_auto_jewels: int
    blue_auto_glyphs: int
    blue_auto_keys: int
    blue_auto_parks: int
    blue_tele_glyphs: int
    blue_tele_rows: int
    blue_tele_cols: int
    blue_tele_cyphers: int
    blue_end_relic_1: int
    blue_end_relic_2: int
    blue_end_relic_3: int
    blue_end_relic_standing: int
    blue_end_robot_balances: int


class RoverRuckusMatchDetails(BaseMatchDetails):
    red_auto_land: int
    red_auto_samp: int
    red_auto_claim: int
    red_auto_park: int
    red_tele_gold: int
    red_tele_silver: int
    red_tele_depot: int
    red_end_latch: int
    red_end_in: int
    red_end_comp: int
    blue_auto_land: int
    blue_auto_samp: int
    blue_auto_claim: int
    blue_auto_park: int
    blue_tele_gold: int
    blue_tele_silver: int
    blue_tele_depot: int
    blue_end_latch: int
    blue_end_in: int
    blue_end_comp: int


class MatchDetails(Converter):
    def __call__(self, data):
        return {"1617": VelocityVortexMatchDetails,
                "1718": RelicRecoveryMatchDetails,
                "1819": RoverRuckusMatchDetails}.get(data["match_detail_key"][:4], BaseMatchDetails)(data)


class Ranking(Model):
    rank_key: str
    event_key: str
    team_key: str
    rank: int
    rank_change: int
    wins: int
    losses: int
    ties: int
    highest_qual_score: int
    ranking_points: int
    qualifying_points: int
    tie_breaker_points: int
    disqualified: int
    played: int


class Team(Model):
    team_key: str
    region_key: str
    league_key: str
    team_number: int
    team_name_short: str
    team_name_long: str
    robot_name: str
    last_active: str
    city: str
    state_prov: str
    zip_code: str
    country: str
    rookie_year: int
    website: str


class TeamEventParticipant(Model):
    event_participant_key: str
    event_key: str
    team_key: str
    team_number: int
    is_active: bool
    card_status: str
    team: Team


class EventEventParticipant(Model):
    event_participant_key: str
    event_key: str
    team_key: str
    is_active: bool
    card_status: str
    event: Event



class Award(Model):
    award_key: str
    award_type: int
    award_description: str
    display_order: int


class AwardRecipient(Model):
    awards_key: str
    event_key: str
    award_key: str
    team_key: str
    receiver_name: str
    award_name: str
    award: Award


def to_model(data, model):
    if model is Any:
        return data # don't even touch it

    # this is a ghetto check for things like List[int] or smth
    # duck typing amirite
    if hasattr(model, "__origin__"):

        # the in expr is for 3.6 compat REEEEEEEEEEEEEEEE
        if model.__origin__ in (list, List):
            return [to_model(d, model.__args__[0]) for d in data]
        elif model.__origin__ in (dict, Dict):
            return {to_model(k, model.__args__[0]): to_model(v, model.__args__[1]) for k, v in data.items()}

    # usually you can just call otherwise lol
    # if the data endpoint is None, chances are calling a model on it will fail, so we can just return None
    return model(data) if data is not None else None

