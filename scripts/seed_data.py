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
            {"name": "Serie A", "type": "DOMESTIC", "logo_path": "https://media.api-sports.io/football/leagues/135.png"},
            {"name": "Bundesliga", "type": "DOMESTIC", "logo_path": "https://media.api-sports.io/football/leagues/78.png"},
            {"name": "Ligue 1", "type": "DOMESTIC", "logo_path": "https://media.api-sports.io/football/leagues/61.png"},
            {"name": "MLS", "type": "DOMESTIC", "logo_path": "https://media.api-sports.io/football/leagues/253.png"},
            {"name": "Champions League", "type": "INTERNATIONAL", "logo_path": "https://media.api-sports.io/football/leagues/2.png"},
            {"name": "Europa League", "type": "INTERNATIONAL", "logo_path": "https://media.api-sports.io/football/leagues/3.png"},
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
            {"name": "Manchester United", "is_national": False, "league_id": league_map["Premier League"]},
            {"name": "Tottenham", "is_national": False, "league_id": league_map["Premier League"]},
            
            {"name": "Real Madrid", "is_national": False, "league_id": league_map["La Liga"]},
            {"name": "Barcelona", "is_national": False, "league_id": league_map["La Liga"]},
            {"name": "Atletico Madrid", "is_national": False, "league_id": league_map["La Liga"]},
            
            {"name": "Juventus", "is_national": False, "league_id": league_map["Serie A"]},
            {"name": "AC Milan", "is_national": False, "league_id": league_map["Serie A"]},
            {"name": "Inter Milan", "is_national": False, "league_id": league_map["Serie A"]},
            {"name": "Napoli", "is_national": False, "league_id": league_map["Serie A"]},
            
            {"name": "Bayern Munich", "is_national": False, "league_id": league_map["Bundesliga"]},
            {"name": "Borussia Dortmund", "is_national": False, "league_id": league_map["Bundesliga"]},
            {"name": "Bayer Leverkusen", "is_national": False, "league_id": league_map["Bundesliga"]},
            
            {"name": "PSG", "is_national": False, "league_id": league_map["Ligue 1"]},
            {"name": "Marseille", "is_national": False, "league_id": league_map["Ligue 1"]},
            {"name": "Monaco", "is_national": False, "league_id": league_map["Ligue 1"]},
            
            {"name": "Inter Miami", "is_national": False, "league_id": league_map["MLS"]},
            {"name": "LA Galaxy", "is_national": False, "league_id": league_map["MLS"]},
            {"name": "New York City FC", "is_national": False, "league_id": league_map["MLS"]},
            
            {"name": "Argentina", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "France", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "Brazil", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "England", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "Spain", "is_national": True, "league_id": league_map["World Cup"]},
            {"name": "Germany", "is_national": True, "league_id": league_map["World Cup"]},
        ]
        
        for t_data in teams_data:
            session.add(Team(**t_data))
            
        await session.commit()
        print("Successfully seeded database!")

if __name__ == "__main__":
    asyncio.run(seed_data())
