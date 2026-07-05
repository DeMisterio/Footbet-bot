import asyncio
import os
import sys

# Add parent directory to path to allow imports from bot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.database import engine, AsyncSessionLocal
from bot.models import Base, League, Team

async def seed_data():
    print("Recreating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("Seeding initial Leagues and Teams...")
    async with AsyncSessionLocal() as session:
        # Create Leagues
        leagues_data = [
            {"name": "Premier League", "type": "DOMESTIC", "logo_path": "https://media.api-sports.io/football/leagues/39.png"},
            {"name": "La Liga", "type": "DOMESTIC", "logo_path": "https://media.api-sports.io/football/leagues/140.png"},
            {"name": "Champions League", "type": "INTERNATIONAL", "logo_path": "https://media.api-sports.io/football/leagues/2.png"},
            {"name": "World Cup", "type": "INTERNATIONAL", "logo_path": "https://media.api-sports.io/football/leagues/1.png"}
        ]
        
        leagues = []
        for l_data in leagues_data:
            league = League(**l_data)
            session.add(league)
            leagues.append(league)
            
        await session.flush()
        
        # Mapping league names to IDs
        league_map = {l.name: l.id for l in leagues}
        
        # Create Teams
        teams_data = [
            {"name": "Arsenal", "is_national": False, "league_id": league_map["Premier League"]},
            {"name": "Manchester City", "is_national": False, "league_id": league_map["Premier League"]},
            {"name": "Liverpool", "is_national": False, "league_id": league_map["Premier League"]},
            {"name": "Chelsea", "is_national": False, "league_id": league_map["Premier League"]},
            
            {"name": "Real Madrid", "is_national": False, "league_id": league_map["La Liga"]},
            {"name": "Barcelona", "is_national": False, "league_id": league_map["La Liga"]},
            {"name": "Atletico Madrid", "is_national": False, "league_id": league_map["La Liga"]},
            
            {"name": "Bayern Munich", "is_national": False, "league_id": league_map["Champions League"]},
            {"name": "PSG", "is_national": False, "league_id": league_map["Champions League"]},
            {"name": "Juventus", "is_national": False, "league_id": league_map["Champions League"]},
            
            {"name": "Argentina", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "France", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "Brazil", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "England", "is_national": True, "league_id": league_map["World Cup"]},
        ]
        
        for t_data in teams_data:
            session.add(Team(**t_data))
            
        await session.commit()
        print("Successfully seeded database!")

if __name__ == "__main__":
    asyncio.run(seed_data())
