import typing

class Column:
    def __init__(self, sql):
        self.sql = sql


if typing.TYPE_CHECKING:
    def varchar(length: int) -> typing.Type[str]:
        return str
else:
    def varchar(length: int) -> Column:
        return Column(f'varchar({length})')

if typing.TYPE_CHECKING:
    integer = int2 = int4 = int8 = smallint = bigint = int
    text = str
    real = double_precision = float
    boolean = bool
else:
    integer = Column('integer')
    int2 = Column('int2')
    int4 = Column('int4')
    int8 = Column('int8')
    smallint = Column('smallint')
    bigint = Column('bigint')
    text = Column('text')
    real = Column('real')
    double_precision = Column('double precision')
    timestamp = Column('timestamp')
    boolean = Column('boolean')
