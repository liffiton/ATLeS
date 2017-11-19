from pathlib import Path

from sqlalchemy import MetaData, Table, Column, Integer, Float, String, Boolean, DateTime, ForeignKey
import sqlalchemy.types as types

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
    Column('exp_runtime', Integer),
    Column('last_updated', Integer)
)


class PathType(types.TypeDecorator):
    ''' Stores pathlib.Path objects as Strings in the db,
        converting on reads and writes. '''

    impl = types.String

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return Path(value)


tracks = Table(
    'tracks',
    metadata,
    Column('key', String, primary_key=True),
    Column('trackpath', PathType),
    Column('trackrel', String),
    Column('setupfile', PathType),
    Column('box', String, index=True),
    Column('exp_name', String, index=True),
    Column('starttime', DateTime),
    Column('trigger', String),
    Column('controller', String),
    Column('stimulus', String),
    Column('did_stim', Boolean),  # did any of the phases activate the conditional stimulus?
    Column('notes', String),
    Column('lines', Integer),
    Column('acquired', Float),
    Column('sketchy', Float),
    Column('missing', Float),
    Column('lost', Float),
    Column('heat', String),  # string-encoded position heatmap
    Column('invalid_heat', String)  # same, but for positions of invalid points
)

phases = Table(
    'phases',
    metadata,
    Column('track_key', String, ForeignKey("tracks.key"), index=True, nullable=False),
    Column('phase_num', Integer, nullable=False),
    Column('phase_len', Integer, nullable=False),
    Column('stim_actual', String, nullable=False)
)


def create_all(engine):
    metadata.create_all(engine)
