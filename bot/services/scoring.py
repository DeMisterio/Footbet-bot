from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import Match, Prediction, User, SquadMember, SquadTeam

async def distribute_points(match_id: int, home_score: int, away_score: int):
    if home_score > away_score:
        actual_winner = "HOME"
    elif away_score > home_score:
        actual_winner = "AWAY"
    else:
        actual_winner = "DRAW"
        
    actual_score = f"{home_score}-{away_score}"
    
    async with AsyncSessionLocal() as session:
        # Get all predictions for this match
        result = await session.execute(
            select(Prediction).where(Prediction.match_id == match_id)
        )
        predictions = result.scalars().all()
        
        for prediction in predictions:
            points_to_award = 0
            
            # Check winner
            if prediction.predicted_winner == actual_winner:
                points_to_award += 10
                
            # Check exact score
            if prediction.predicted_score == actual_score:
                points_to_award += 5
                
            if points_to_award > 0:
                prediction.points_awarded = points_to_award
                
                # Update points for the user in EVERY team that tracked this match
                squad_member_query = (
                    select(SquadMember)
                    .join(SquadTeam, SquadMember.squad_id == SquadTeam.squad_id)
                    .join(Match, (SquadTeam.team_id == Match.home_team_id) | (SquadTeam.team_id == Match.away_team_id))
                    .where(Match.id == match_id, SquadMember.user_id == prediction.user_id)
                )
                
                squad_members_res = await session.execute(squad_member_query)
                squad_members = squad_members_res.scalars().all()
                
                for sm in squad_members:
                    sm.points += points_to_award
                    
        await session.commit()
    
    return True
