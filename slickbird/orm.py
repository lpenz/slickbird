'''ORM'''

import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class AsDict(object):

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Collection(Base, AsDict):
    __tablename__ = 'collection'
    id = sqla.Column(
        sqla.Integer, sqla.Sequence('collection_id_seq'), primary_key=True)
    name = sqla.Column(sqla.String(50))
    directory = sqla.Column(sqla.String(50))
    filename = sqla.Column(sqla.String(50))
    status = sqla.Column(sqla.String(50))


class Game(Base, AsDict):
    __tablename__ = 'game'
    id = sqla.Column(sqla.Integer, primary_key=True)
    collection_id = sqla.Column(
        sqla.Integer, sqla.ForeignKey('collection.id'))
    collection = relationship(
        'Collection', backref=backref('games', order_by=id))
    name = sqla.Column(sqla.String(50))
    description = sqla.Column(sqla.String(200))
    status = sqla.Column(sqla.String(50))


class Variant(Base, AsDict):
    __tablename__ = 'variant'
    id = sqla.Column(sqla.Integer, primary_key=True)
    game_id = sqla.Column(
        sqla.Integer, sqla.ForeignKey('game.id'))
    game = relationship(
        'Game', backref=backref('variants', order_by=id))
    name = sqla.Column(sqla.String(50))


class Rom(Base, AsDict):
    __tablename__ = 'rom'
    id = sqla.Column(sqla.Integer, primary_key=True)
    variant_id = sqla.Column(
        sqla.Integer, sqla.ForeignKey('variant.id'))
    variant = relationship(
        'Variant', backref=backref('roms', order_by=id))
    filename = sqla.Column(sqla.String(80))
    size = sqla.Column(sqla.Integer)
    crc = sqla.Column(sqla.String(8))
    status = sqla.Column(sqla.String(50))


class Importerfile(Base, AsDict):
    __tablename__ = 'importerfile'
    id = sqla.Column(sqla.Integer, primary_key=True)
    filename = sqla.Column(sqla.String(80))
    status = sqla.Column(sqla.String(50))


# Session: ###################################################################

def make_session(database):
    engine = sqla.create_engine(database, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session
