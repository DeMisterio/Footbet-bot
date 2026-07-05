import uuid
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import User, Squad, SquadMember
from bot.i18n import _

router = Router()

from bot.handlers.menu import get_main_keyboard

class OnboardingStates(StatesGroup):
    waiting_for_invite_code = State()

@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    
    # Check if user exists, otherwise create
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=message.from_user.id, language=message.from_user.language_code or 'en')
            session.add(user)
            await session.commit()
    
    # Send persistent main menu first
    await message.answer("Welcome to Footbet! ⚽️", reply_markup=get_main_keyboard())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("JOIN TEAM"), callback_data="onboard_join_team")],
        [InlineKeyboardButton(text=_("CREATE TEAM"), callback_data="onboard_create_team")]
    ])
    
    await message.answer(
        _("Do you want to join an existing team or create a new one?"),
        reply_markup=keyboard
    )

@router.message(F.text == "➕ Join/Create Squad")
async def handle_join_create_menu(message: Message, state: FSMContext):
    # This mirrors the onboarding prompt when using the persistent menu
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("JOIN TEAM"), callback_data="onboard_join_team")],
        [InlineKeyboardButton(text=_("CREATE TEAM"), callback_data="onboard_create_team")]
    ])
    
    await message.answer(
        _("Do you want to join an existing team or create a new one?"),
        reply_markup=keyboard
    )

@router.callback_query(F.data == "onboard_join_team")
async def join_team_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        _("Please enter the specific INVITATION CODE provided by your team admin:")
    )
    await state.set_state(OnboardingStates.waiting_for_invite_code)
    await callback.answer()

@router.callback_query(F.data == "onboard_create_team")
async def create_team_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    invite_code = str(uuid.uuid4())[:8].upper()
    bot_username = (await callback.bot.me()).username
    invite_link = f"https://t.me/{bot_username}?start={invite_code}"
    
    async with AsyncSessionLocal() as session:
        new_squad = Squad(admin_id=user_id, invite_code=invite_code, invite_link=invite_link)
        session.add(new_squad)
        await session.commit()
        await session.refresh(new_squad)
        
        # Add user as member
        member = SquadMember(user_id=user_id, squad_id=new_squad.id)
        session.add(member)
        await session.commit()
        
    await callback.message.edit_text(
        _("Team created successfully! You are the admin.\n\n"
          "Your unique INVITATION CODE: {invite_code}\n"
          "Direct Telegram invite link: {invite_link}\n\n"
          "Share this code or link with your friends to invite them into the squad.").format(
              invite_code=invite_code, invite_link=invite_link
          )
    )
    await callback.answer()

@router.message(OnboardingStates.waiting_for_invite_code)
async def process_invite_code(message: Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Squad).where(Squad.invite_code == code))
        squad = result.scalar_one_or_none()
        
        if not squad:
            await message.answer(_("Invalid INVITATION CODE. Please try again or type /start to go back."))
            return
            
        # Check if already a member
        res_member = await session.execute(
            select(SquadMember).where(SquadMember.squad_id == squad.id, SquadMember.user_id == user_id)
        )
        if res_member.scalar_one_or_none():
            await message.answer(_("You are already a member of this team!"))
        else:
            member = SquadMember(user_id=user_id, squad_id=squad.id)
            session.add(member)
            await session.commit()
            await message.answer(_("You have successfully joined the team!"))
            
    await state.clear()
