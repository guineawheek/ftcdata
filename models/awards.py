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
    THINK = 2
    CONNECT = 3
    INNOVATE = 4
    DESIGN = 5
    MOTIVATE = 6
    CONTROL = 7
    JUDGES = 8
    PROMOTE = 9
    COMPASS = 10
    DEANS_LIST_W = 11
    DEANS_LIST_F = 12
    DEANS_LIST_SF = 13
    CUSTOM = -1

    base_names = {
            INSPIRE: "Inspire Award",
            THINK: "Think Award",
            CONNECT: "Connect Award",
            INNOVATE: "Innovate Award", 
            DESIGN: "Design Award",
            MOTIVATE: "Motivate Award",
            CONTROL: "Control Award",
            JUDGES: "Judge's Award",
            PROMOTE: "Promote Award",
            COMPASS: "Compass Award",
            DEANS_LIST_W: "Dean's List Winner",
            DEANS_LIST_F: "Dean's List Finalist",
            DEANS_LIST_SF: "Dean's List Semifinalist",
    }
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
