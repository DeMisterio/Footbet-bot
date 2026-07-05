import os
import sys
import asyncio
from pathlib import Path
from PIL import Image
from sqlalchemy import select

# Add bot to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import AsyncSessionLocal, engine
from bot.models import Base, Team, League

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "badges"
OPTIMIZED_DIR = Path(__file__).parent.parent / "assets" / "optimized_logos"

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def clean_name(filename):
    name = Path(filename).stem
    
    name = name.replace(".football-logos.cc", "")
    name = name.replace("-national-team", "")
    name = name.replace("national-team", "")
    name = name.replace("[CITYPNG.COM]", "")
    name = name.replace("HD ", "")
    name = name.replace("Icon", "")
    name = name.replace("White", "")
    name = name.replace("Black", "")
    name = name.replace("Logo", "")
    name = name.replace("Transparent", "")
    name = name.replace("Background", "")
    name = name.replace("tournaments_", "")
    name = name.replace("3000x3000", "")
    
    if "-" in name and "x" in name.split("-")[-1] and name.split("-")[-1].replace("x", "").isdigit():
        name = "-".join(name.split("-")[:-1])
            
    name = name.replace("-", " ")
    return name.strip().title()

def optimize_image(source_path, target_path):
    try:
        with Image.open(source_path) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            img.save(target_path, "PNG", optimize=True)
            return True
    except Exception as e:
        print(f"Failed to optimize {source_path}: {e}")
        return False

async def get_or_create_league(session, name: str, league_type: str):
    result = await session.execute(select(League).where(League.name == name))
    league = result.scalar_one_or_none()
    if not league:
        league = League(name=name, type=league_type)
        session.add(league)
        await session.flush()
    return league

async def audit_logos():
    print("Starting logo audit...")
    await init_db()
    
    os.makedirs(OPTIMIZED_DIR, exist_ok=True)
    
    async with AsyncSessionLocal() as session:
        # Pre-create international and domestic fallback leagues
        intl_league = await get_or_create_league(session, "FIFA International", "INTERNATIONAL")
        dom_league = await get_or_create_league(session, "Generic Domestic", "DOMESTIC")
        
        for root, _, files in os.walk(ASSETS_DIR):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg", ".svg")) and not file.startswith("."):
                    if file.endswith(".svg"):
                        continue
                        
                    source_path = os.path.join(root, file)
                    name = clean_name(file)
                    
                    if not name:
                        continue
                        
                    is_national = "National teams" in root
                    is_league = "Leagues" in root
                    
                    target_filename = f"{name.lower().replace(' ', '_')}.png"
                    target_path = os.path.join(OPTIMIZED_DIR, target_filename)
                    
                    success = optimize_image(source_path, target_path)
                    
                    if success:
                        relative_path = os.path.relpath(target_path, ASSETS_DIR.parent)
                        
                        if is_league:
                            # It's a tournament/league logo
                            league_type = "INTERNATIONAL" if "World Cup" in name or "Euro" in name else "DOMESTIC"
                            result = await session.execute(select(League).where(League.name == name))
                            existing_league = result.scalar_one_or_none()
                            if existing_league:
                                existing_league.logo_path = relative_path
                            else:
                                session.add(League(name=name, type=league_type, logo_path=relative_path))
                            print(f"Processed League: {name}")
                        else:
                            # It's a team
                            result = await session.execute(select(Team).where(Team.name == name))
                            existing_team = result.scalar_one_or_none()
                            
                            assigned_league = intl_league.id if is_national else dom_league.id
                            
                            if existing_team:
                                existing_team.logo_path = relative_path
                                existing_team.is_national = is_national
                                existing_team.league_id = assigned_league
                            else:
                                session.add(Team(
                                    name=name,
                                    logo_path=relative_path,
                                    is_national=is_national,
                                    league_id=assigned_league
                                ))
                            print(f"Processed Team: {name} (League ID: {assigned_league})")
                            
        await session.commit()
    print("Logo audit complete.")

if __name__ == "__main__":
    asyncio.run(audit_logos())
