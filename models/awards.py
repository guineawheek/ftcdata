from db.orm import orm
from db.types import *

__all__ = ["Award", "AwardType"]
class Award(orm.Model):
    __tablename__ = "awards"
    __primary_key__ = ("event_key", "award_type", "award_place", "team_key")
    name: text
    award_type: integer
    award_place: integer
    event_key: text
    team_key: text
    # for awards given to real people like Dean's List or Compass
    recipient_name: text

class AwardType:
    INSPIRE = 1
    WINNING_ALLIANCE = 2
    FINALIST_ALLIANCE = 3
    THINK = 4
    CONNECT = 5
    INNOVATE = 6
    DESIGN = 7
    MOTIVATE = 8
    CONTROL = 9
    JUDGES = 10
    PROMOTE = 11
    COMPASS = 12
    VOL_OF_YEAR = 13
    DEANS_LIST_W = 14
    DEANS_LIST_F = 15
    DEANS_LIST_SF = 16
    CUSTOM = 9999

    base_names = {
        INSPIRE: "Inspire Award",
        WINNING_ALLIANCE: "Winner",
        FINALIST_ALLIANCE: "Finalist",
        THINK: "Think Award",
        CONNECT: "Connect Award",
        INNOVATE: "Innovate Award",
        DESIGN: "Design Award",
        MOTIVATE: "Motivate Award",
        CONTROL: "Control Award",
        JUDGES: "Judge's Award",
        PROMOTE: "Promote Award",
        COMPASS: "Compass Award",
        VOL_OF_YEAR: "Volunteer of The Year",
        DEANS_LIST_W: "Dean's List Winner",
        DEANS_LIST_F: "Dean's List Finalist",
        DEANS_LIST_SF: "Dean's List Semifinalist",
    }
    to_type = {
        "inspire": INSPIRE,
        "think": THINK,
        "connect": CONNECT,
        "innovate": INNOVATE,
        "rockwell collins innovate": INNOVATE,
        "collins aerospace innovate": INNOVATE,
        "design": DESIGN,
        "ptc design": DESIGN,
        "motivate": MOTIVATE,
        "control": CONTROL,
        "judge's": JUDGES,
        "judges'": JUDGES,
        "promote": PROMOTE,
        "compass": COMPASS,
        "volunteer": VOL_OF_YEAR,
    }

    @classmethod
    def get_type(cls, name):
        name = name.lower()
        sname = name.split()
        if sname[-1] == 'award':
            name = ' '.join(sname[:-1])
        return cls.to_type.get(name.lower(), cls.CUSTOM)

    @classmethod
    def get_names(cls, const, given="", year=2018):
        base = cls.base_names.get(const, given)
        if const == cls.INNOVATE:
            # Rockwell Collins -> Collins Aerospace for 2018-2019+
            return ("Collins Aerospace " if year > 2017 else "Rockwell Collins ") + base
        elif const == cls.DESIGN and year < 2017:
            # PTC got dropped after 2016-2017
            return "PTC " + base
        return base
