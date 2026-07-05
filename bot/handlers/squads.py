from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import Squad, SquadMember, User

squads_router = Router()

# --- SQUAD VIEWING ---

@squads_router.message(F.text == "🏆 My Squads")
async def list_my_squads(message: Message):
    async with AsyncSessionLocal() as session:
        # Fetch squads user is in
        res = await session.execute(
            select(Squad).join(SquadMember).where(SquadMember.user_id == message.from_user.id)
        )
        squads = res.scalars().all()
        
        if not squads:
            await message.answer("You are not in any squads yet.")
            return
            
        # Create inline keyboard for squads
        buttons = []
        for s in squads:
            buttons.append([InlineKeyboardButton(text=s.invite_code, callback_data=f"view_squad_{s.id}")])
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Select a squad to view the leaderboard:", reply_markup=keyboard)

@squads_router.callback_query(F.data.startswith("view_squad_"))
async def view_squad_leaderboard(callback: CallbackQuery):
    squad_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        # Fetch members ordered by points
        res = await session.execute(
            select(SquadMember, User)
            .join(User, SquadMember.user_id == User.id)
            .where(SquadMember.squad_id == squad_id)
            .order_by(SquadMember.points.desc())
        )
        records = res.all()
        
        text = "🏆 **Leaderboard**\n\n"
        for i, (member, user) in enumerate(records, 1):
            text += f"{i}. User `{user.id}` - {member.points} pts\n"
            
        # Setup back button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Squads", callback_data="back_to_squads")]
        ])
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()

@squads_router.callback_query(F.data == "back_to_squads")
async def back_to_squads_handler(callback: CallbackQuery):
    # Reuse list logic
    await callback.message.delete()
    await list_my_squads(callback.message)
    await callback.answer()
