'''ORM'''

import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class AsDict(object):

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Collection(Base, AsDict):
    __tablename__ = 'collection'
    id = sqla.Column(
        sqla.Integer, sqla.Sequence('collection_id_seq'), primary_key=True)
    name = sqla.Column(sqla.String(50))
    filename = sqla.Column(sqla.String(50))
    status = sqla.Column(sqla.String(50))

    def __repr__(self):
        return "<Collection(name='%s')>" % (
            self.name)


class Game(Base, AsDict):
    __tablename__ = 'game'
    id = sqla.Column(sqla.Integer, primary_key=True)
    collection_id = sqla.Column(
        sqla.Integer, sqla.ForeignKey('collection.id'))
    collection = relationship(
        'Collection', backref=backref('games', order_by=id))
    name = sqla.Column(sqla.String(50))
    status = sqla.Column(sqla.String(50))

    def __repr__(self):
        return "<Game(name='%s')>" % self.name


class Rom(Base):
    __tablename__ = 'rom'
    id = sqla.Column(sqla.Integer, primary_key=True)
    game_id = sqla.Column(
        sqla.Integer, sqla.ForeignKey('game.id'))
    game = relationship(
        'Game', backref=backref('roms', order_by=id))
    filename = sqla.Column(sqla.String(80))
    size = sqla.Column(sqla.Integer)
    crc = sqla.Column(sqla.String(8))
    md5 = sqla.Column(sqla.String(32))
    sha1 = sqla.Column(sqla.String(40))
    status = sqla.Column(sqla.String(50))

    def __repr__(self):
        return "<Rom(filename='%s')>" % self.filename


class Scannerfile(Base, AsDict):
    __tablename__ = 'scannerfile'
    id = sqla.Column(sqla.Integer, primary_key=True)
    filename = sqla.Column(sqla.String(80))
    status = sqla.Column(sqla.String(50))

    def __repr__(self):
        return "<Scannerfile(filename='%s')>" % self.filename

# Session: ###################################################################

from sqlalchemy.orm import sessionmaker


def make_session(database):
    engine = sqla.create_engine(database, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session
