from sqlalchemy import Table, Column, Integer, Float, String, Boolean, DateTime, MetaData

metadata = MetaData()

boxes = Table(
    'boxes',
    metadata,
    Column('name', String, primary_key=True),
    Column('ip', String, nullable=False),
    Column('port', Integer, nullable=False),
    Column('local', Boolean),
    Column('user', String),
    Column('connected', Boolean),
    Column('hasdisplay', Boolean),
    Column('gitshort', String),
    Column('gitlong', String),
    Column('error', String),
    Column('latest_local_datafile', DateTime),
    Column('exp_running', Boolean),
    Column('exp_pid', Integer),
    Column('exp_starttime', Integer),
    Column('exp_runtime', Integer)
)

tracks = Table(
    'tracks',
    metadata,
    Column('key', String, primary_key=True),
    Column('trackpath', String),
    Column('trackrel', String),
    Column('box', String),
    Column('starttime', DateTime),
    Column('exp_name', String),
    Column('lines', Integer),
    Column('acquired', Float),
    Column('sketchy', Float),
    Column('missing', Float),
    Column('lost', Float),
    Column('heat', String),
    Column('invalid_heat', String)
)


def create_all(engine):
    metadata.create_all(engine)
