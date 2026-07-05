from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import SquadMember, SquadTeam, Match

async def get_users_to_notify_for_match(match_id: int):
    """
    Notification Deduplication Engine
    Queries DISTINCT users who should receive a notification for a specific match.
    A user is notified if they are part of AT LEAST ONE team (squad) that:
      1. Has notifications_muted = False for that user.
      2. Is tracking either the home or away team of the match.
    Uses SQL DISTINCT to ensure exactly one notification per user regardless of how many squads they are in.
    """
    async with AsyncSessionLocal() as session:
        query = (
            select(SquadMember.user_id)
            .join(SquadTeam, SquadMember.squad_id == SquadTeam.squad_id)
            .join(Match, (SquadTeam.team_id == Match.home_team_id) | (SquadTeam.team_id == Match.away_team_id))
            .where(Match.id == match_id, SquadMember.notifications_muted == False)
            .distinct()
        )
        
        result = await session.execute(query)
        user_ids = result.scalars().all()
        
        return user_ids

async def broadcast_match_notification(bot, match_id: int, text: str, reply_markup=None):
    """
    Broadcasts a notification to all relevant users without duplication.
    """
    user_ids = await get_users_to_notify_for_match(match_id)
    
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=text, reply_markup=reply_markup)
        except Exception as e:
            # Handle user blocked bot, etc.
            print(f"Failed to send to {uid}: {e}")
