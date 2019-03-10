from db.orm import orm
from db.types import *

class Award(orm.Model):
    __tablename__ = "awards"
    __primary_key__ = ("event_key", "award_type")
    name: text
    award_type: integer
    event_key: varchar(32)
    recipient_list: Column("varchar(20)[]")
    # for awards given to teams
    recipient_names: Column("text[]")
