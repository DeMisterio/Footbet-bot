from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True, index=True) # Telegram User ID
    language = Column(String(10), default='en')
    total_points = Column(Integer, default=0)

    squads = relationship('SquadMember', back_populates='user')
    predictions = relationship('Prediction', back_populates='user')

class Squad(Base):
    __tablename__ = 'squads'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    admin_id = Column(BigInteger, ForeignKey('users.id'))
    invite_code = Column(String(50), unique=True, index=True)
    invite_link = Column(String(200))
    
    admin = relationship('User', foreign_keys=[admin_id])
    members = relationship('SquadMember', back_populates='squad')
    tracked_teams = relationship('SquadTeam', back_populates='squad')

class SquadMember(Base):
    __tablename__ = 'squad_members'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    squad_id = Column(Integer, ForeignKey('squads.id'))
    points = Column(Integer, default=0)
    notifications_muted = Column(Boolean, default=False)
    
    user = relationship('User', back_populates='squads')
    squad = relationship('Squad', back_populates='members')

class League(Base):
    __tablename__ = 'leagues'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True)
    type = Column(String(50)) # 'DOMESTIC' or 'INTERNATIONAL'
    logo_path = Column(String(255), nullable=True)

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True)
    logo_path = Column(String(255))
    is_national = Column(Boolean, default=False)
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=True)
    
    league = relationship('League')
    
class SquadTeam(Base):
    __tablename__ = 'squad_teams'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    squad_id = Column(Integer, ForeignKey('squads.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    
    squad = relationship('Squad', back_populates='tracked_teams')
    team = relationship('Team')

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, index=True) # API Match ID
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=True)
    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))
    start_time = Column(DateTime)
    status = Column(String(50)) # e.g. 'SCHEDULED', 'LIVE', 'FINISHED'
    is_knockout = Column(Boolean, default=False)
    home_win_prob = Column(Float, nullable=True)
    draw_prob = Column(Float, nullable=True)
    away_win_prob = Column(Float, nullable=True)
    
    home_team = relationship('Team', foreign_keys=[home_team_id])
    away_team = relationship('Team', foreign_keys=[away_team_id])

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    predicted_winner = Column(String(20)) # 'HOME', 'AWAY', 'DRAW'
    predicted_score = Column(String(10), nullable=True) # e.g. '2-1'
    points_awarded = Column(Integer, default=0)
    
    user = relationship('User', back_populates='predictions')
    match = relationship('Match')
