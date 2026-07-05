from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import Match, Prediction, Team
import os

predictions_router = Router()

class ExactScoreState(StatesGroup):
    waiting_for_score = State()

@predictions_router.message(F.text == "📅 Upcoming Matches")
async def list_matches(message: Message):
    async with AsyncSessionLocal() as session:
        # Get active matches (mock logic: limit 5)
        res = await session.execute(
            select(Match).where(Match.status == "SCHEDULED").limit(5)
        )
        matches = res.scalars().all()
        
        if not matches:
            await message.answer("No upcoming matches found.")
            return
            
        for match in matches:
            # Get teams
            home = await session.get(Team, match.home_team_id)
            away = await session.get(Team, match.away_team_id)
            
            text = f"⚽️ **{home.name} vs {away.name}**\n🕒 {match.start_time.strftime('%Y-%m-%d %H:%M')}"
            if match.is_knockout:
                text += "\n⚠️ **KNOCKOUT PHASE**"
                
            buttons = [
                InlineKeyboardButton(text="🏠 Home Win", callback_data=f"predict_{match.id}_HOME"),
            ]
            if not match.is_knockout:
                buttons.append(InlineKeyboardButton(text="🤝 Draw", callback_data=f"predict_{match.id}_DRAW"))
            buttons.append(InlineKeyboardButton(text="✈️ Away Win", callback_data=f"predict_{match.id}_AWAY"))
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            
            # Send photo if exists in cache (mock implementation path)
            photo_path = f"assets/cache/{match.id}_vs.png"
            if os.path.exists(photo_path):
                photo = FSInputFile(photo_path)
                await message.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@predictions_router.callback_query(F.data.startswith("predict_"))
async def handle_winner_prediction(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    match_id = int(parts[1])
    winner = parts[2]
    
    # Store preliminary prediction in state
    await state.update_data(match_id=match_id, winner=winner)
    
    # Ask for exact score
    await callback.message.answer(
        f"You predicted **{winner}**. \n\n"
        "Do you want to predict the exact score for +5 bonus points?\n"
        "Reply with the score (e.g. `2-1`) or click Skip.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip Exact Score", callback_data="skip_exact_score")]
        ])
    )
    await state.set_state(ExactScoreState.waiting_for_score)
    await callback.answer()

async def save_prediction(user_id: int, match_id: int, winner: str, exact_score: str = None):
    async with AsyncSessionLocal() as session:
        # Upsert logic
        res = await session.execute(
            select(Prediction).where(Prediction.user_id == user_id, Prediction.match_id == match_id)
        )
        prediction = res.scalar_one_or_none()
        
        if prediction:
            prediction.predicted_winner = winner
            prediction.predicted_score = exact_score
        else:
            prediction = Prediction(
                user_id=user_id,
                match_id=match_id,
                predicted_winner=winner,
                predicted_score=exact_score
            )
            session.add(prediction)
            
        await session.commit()

@predictions_router.message(ExactScoreState.waiting_for_score)
async def process_exact_score(message: Message, state: FSMContext):
    score = message.text.strip()
    # Simple validation regex or check
    if "-" not in score or len(score) > 5:
        await message.answer("Invalid format. Please use format like `2-1` or click Skip.")
        return
        
    data = await state.get_data()
    await save_prediction(message.from_user.id, data['match_id'], data['winner'], score)
    
    await message.answer(f"✅ Prediction locked in: **{data['winner']}** with exact score **{score}**!", parse_mode="Markdown")
    await state.clear()

@predictions_router.callback_query(F.data == "skip_exact_score")
async def skip_exact_score(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Check if we are actually waiting for a score
    current_state = await state.get_state()
    if current_state == ExactScoreState.waiting_for_score.state:
        await save_prediction(callback.from_user.id, data['match_id'], data['winner'], None)
        await callback.message.edit_text(f"✅ Prediction locked in: **{data['winner']}** (No exact score).", parse_mode="Markdown")
        await state.clear()
    await callback.answer()
