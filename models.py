from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    aomtg_url = Column(String)
    has_artstation = Column(Boolean)
    artstation_url = Column(String)
    has_other = Column(Boolean)
    other_url = Column(String)
    supertypes = Column(PickleType)
    types = Column(PickleType)
    subtypes = Column(PickleType)
    works = relationship("Work", back_populates="artist")

class Work(Base):
    __tablename__ = "works"
    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    name = Column(String)
    set_ = Column(String)
    on_aomtg = Column(Boolean)
    aomtg_url = Column(String)
    on_artstation = Column(Boolean)
    artstation_url = Column(String)
    on_reddit = Column(String)
    subreddits = Column(PickleType)
    reddit_urls = Column(PickleType)
    on_other = Column(Boolean)
    other_url = Column(String)
    scryfall_urls = Column(PickleType)
    artist = relationship("Artist", back_populates="works")

engine = create_engine("sqlite:///database.db")
Base.metadata.create_all(engine)