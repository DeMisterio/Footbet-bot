from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import Prediction, Match
from bot.i18n import _

router = Router()

class PredictionStates(StatesGroup):
    waiting_for_exact_score = State()

def get_prediction_keyboard(match_id: int):
    # Team 1, Draw, Team 2
    # Wide button for Exact Score
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=_("Team 1"), callback_data=f"pred_win_HOME_{match_id}"),
            InlineKeyboardButton(text=_("Draw"), callback_data=f"pred_win_DRAW_{match_id}"),
            InlineKeyboardButton(text=_("Team 2"), callback_data=f"pred_win_AWAY_{match_id}")
        ],
        [
            InlineKeyboardButton(text=_("Predict Exact Score"), callback_data=f"pred_score_{match_id}")
        ]
    ])
    return keyboard

@router.callback_query(F.data.startswith("pred_win_"))
async def predict_winner_cb(callback: CallbackQuery):
    _, winner, match_id_str = callback.data.split("_")[1:]
    match_id = int(match_id_str)
    user_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        # Get or create prediction
        result = await session.execute(
            select(Prediction).where(Prediction.user_id == user_id, Prediction.match_id == match_id)
        )
        prediction = result.scalar_one_or_none()
        
        if prediction:
            prediction.predicted_winner = winner
        else:
            prediction = Prediction(user_id=user_id, match_id=match_id, predicted_winner=winner)
            session.add(prediction)
        
        await session.commit()
    
    await callback.answer(_("Prediction for winner registered: {winner}").format(winner=winner), show_alert=True)

@router.callback_query(F.data.startswith("pred_score_"))
async def predict_score_cb(callback: CallbackQuery, state: FSMContext):
    match_id = int(callback.data.split("_")[2])
    await state.update_data(match_id=match_id)
    await state.set_state(PredictionStates.waiting_for_exact_score)
    
    await callback.message.answer(
        _("Please enter your exact score prediction in the format 'HOME-AWAY' (e.g., '2-1').")
    )
    await callback.answer()

@router.message(PredictionStates.waiting_for_exact_score)
async def process_exact_score(message: Message, state: FSMContext):
    data = await state.get_data()
    match_id = data.get("match_id")
    user_id = message.from_user.id
    score_text = message.text.strip()
    
    # Parse score
    if "-" not in score_text:
        await message.answer(_("Invalid format. Please use 'HOME-AWAY' (e.g., '2-1')."))
        return
        
    parts = score_text.split("-")
    if len(parts) != 2 or not parts[0].strip().isdigit() or not parts[1].strip().isdigit():
        await message.answer(_("Invalid format. Please use 'HOME-AWAY' (e.g., '2-1')."))
        return
        
    home_score = int(parts[0].strip())
    away_score = int(parts[1].strip())
    
    # Infer winner
    if home_score > away_score:
        inferred_winner = "HOME"
    elif away_score > home_score:
        inferred_winner = "AWAY"
    else:
        inferred_winner = "DRAW"
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Prediction).where(Prediction.user_id == user_id, Prediction.match_id == match_id)
        )
        prediction = result.scalar_one_or_none()
        
        if prediction:
            prediction.predicted_score = f"{home_score}-{away_score}"
            prediction.predicted_winner = inferred_winner # Overrides manual choice
        else:
            prediction = Prediction(
                user_id=user_id, 
                match_id=match_id, 
                predicted_winner=inferred_winner, 
                predicted_score=f"{home_score}-{away_score}"
            )
            session.add(prediction)
            
        await session.commit()
        
    await message.answer(
        _("Exact score {score} registered! This also sets your winner prediction to {winner}.").format(
            score=f"{home_score}-{away_score}", winner=inferred_winner
        )
    )
    await state.clear()
