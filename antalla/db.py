from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import Session as DBSession
from sqlalchemy.ext.declarative import declarative_base

from . import settings


engine = create_engine(settings.DB_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session: DBSession = scoped_session(Session)
Base = declarative_base()
