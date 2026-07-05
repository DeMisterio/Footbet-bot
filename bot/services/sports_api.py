import os
import time
import aiohttp
import asyncio
import logging
from aiohttp import web
from bot.services.scoring import distribute_points
# Assuming we will have a global bot instance or we can pass it
# from bot.main import bot

logger = logging.getLogger(__name__)

API_KEY = os.getenv("SPORTS_API_KEY", "DEMO_KEY")
BASE_URL = "https://api.example-sports.com/v1"

# Simple in-memory cache to strictly limit API request volume
CACHE = {}
CACHE_TTL = 300 # 5 minutes

async def fetch_match_data(match_id: int):
    # Check cache first
    cache_key = f"match_{match_id}"
    if cache_key in CACHE:
        cached_data, timestamp = CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return cached_data
            
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        try:
            async with session.get(f"{BASE_URL}/matches/{match_id}", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    CACHE[cache_key] = (data, time.time())
                    return data
                else:
                    logger.error(f"Failed to fetch match data: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

# Webhook handler for rapid events like Penalty Shootouts
async def handle_webhook(request):
    try:
        data = await request.json()
        event_type = data.get("event_type")
        match_id = data.get("match_id")
        
        # We need a reference to the bot to send messages
        # Ideally, this runs in the same event loop or app as the bot
        # For demonstration, we'll log it. In bot/main.py we would route this to aiogram
        
        if event_type == "KICKOFF":
            logger.info(f"Match {match_id} started. Send summary message to groups.")
            # Trigger Kick-off notifications
            pass
        elif event_type == "HALFTIME":
            logger.info(f"Match {match_id} halftime. Send updates.")
            pass
        elif event_type == "PENALTY_KICK":
            scored = data.get("scored", False)
            team = data.get("team_name")
            logger.info(f"Penalty for {team}: {'SCORED' if scored else 'MISSED'}!")
            # Broadcast penalty immediately
            pass
        elif event_type == "FULLTIME":
            home_score = data.get("home_score", 0)
            away_score = data.get("away_score", 0)
            is_knockout = data.get("is_knockout", False) # or fetch from DB Match
            
            if is_knockout and home_score == away_score:
                logger.info(f"Knockout Match {match_id} tied {home_score}-{away_score} at FULLTIME. Waiting for AET/PENALTIES.")
                return web.Response(text="Waiting for extra time or penalties")
                
            logger.info(f"Match {match_id} ended {home_score}-{away_score}. Distributing points.")
            await distribute_points(match_id, home_score, away_score)
            
        elif event_type in ["AET", "PENALTY_SHOOTOUT_END"]:
            home_score = data.get("home_score", 0)
            away_score = data.get("away_score", 0)
            logger.info(f"Knockout Match {match_id} ended via {event_type} {home_score}-{away_score}. Distributing points.")
            await distribute_points(match_id, home_score, away_score)
            
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500)

def setup_webhook_app():
    app = web.Application()
    app.router.add_post('/webhook/sports', handle_webhook)
    return app
