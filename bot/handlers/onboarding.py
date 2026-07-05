import uuid
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from bot.database import AsyncSessionLocal
from bot.models import User, Squad, SquadMember, League, Team, SquadTeam
from bot.i18n import _

router = Router()

from bot.handlers.menu import get_main_keyboard

class OnboardingStates(StatesGroup):
    waiting_for_invite_code = State()
    waiting_for_squad_name = State()
    selecting_leagues = State()
    selecting_teams = State()

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

# --- CREATE SQUAD FSM WIZARD ---

@router.callback_query(F.data == "onboard_create_team")
async def create_team_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        _("Let's create your Squad! 🏆\n\nPlease type a name for your squad:")
    )
    await state.set_state(OnboardingStates.waiting_for_squad_name)
    await state.update_data(selected_leagues=[], selected_teams=[])
    await callback.answer()

async def render_leagues_keyboard(session, selected_leagues):
    leagues_res = await session.execute(select(League))
    leagues = leagues_res.scalars().all()
    
    keyboard_buttons = []
    row = []
    for l in leagues:
        mark = "✅ " if l.id in selected_leagues else "⬜️ "
        row.append(InlineKeyboardButton(text=f"{mark}{l.name}", callback_data=f"toggle_league_{l.id}"))
        if len(row) == 2:
            keyboard_buttons.append(row)
            row = []
            
    if row:
        keyboard_buttons.append(row)
        
    keyboard_buttons.append([InlineKeyboardButton(text=_("➡️ Continue"), callback_data="leagues_done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

@router.message(OnboardingStates.waiting_for_squad_name)
async def process_squad_name(message: Message, state: FSMContext):
    squad_name = message.text.strip()
    await state.update_data(squad_name=squad_name)
    
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        kb = await render_leagues_keyboard(session, data.get('selected_leagues', []))
        
    await message.answer(
        _("Great name! Now, please select the Leagues you want your squad to track:"),
        reply_markup=kb
    )
    await state.set_state(OnboardingStates.selecting_leagues)

@router.callback_query(OnboardingStates.selecting_leagues, F.data.startswith("toggle_league_"))
async def toggle_league_cb(callback: CallbackQuery, state: FSMContext):
    league_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = data.get('selected_leagues', [])
    
    if league_id in selected:
        selected.remove(league_id)
    else:
        selected.append(league_id)
        
    await state.update_data(selected_leagues=selected)
    
    async with AsyncSessionLocal() as session:
        kb = await render_leagues_keyboard(session, selected)
        
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

async def render_teams_keyboard(session, league_ids, selected_teams):
    if not league_ids:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=_("✅ Finish"), callback_data="teams_done")]])
        
    teams_res = await session.execute(select(Team).where(Team.league_id.in_(league_ids)))
    teams = teams_res.scalars().all()
    
    keyboard_buttons = []
    # Display in pairs for better UI
    row = []
    for t in teams:
        mark = "✅ " if t.id in selected_teams else "⬜️ "
        row.append(InlineKeyboardButton(text=f"{mark}{t.name}", callback_data=f"toggle_team_{t.id}"))
        if len(row) == 2:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)
        
    keyboard_buttons.append([InlineKeyboardButton(text=_("✅ Finish Setup"), callback_data="teams_done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

@router.callback_query(OnboardingStates.selecting_leagues, F.data == "leagues_done")
async def leagues_done_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_leagues = data.get('selected_leagues', [])
    
    if not selected_leagues:
        await callback.answer(_("Please select at least one league!"), show_alert=True)
        return
        
    async with AsyncSessionLocal() as session:
        kb = await render_teams_keyboard(session, selected_leagues, data.get('selected_teams', []))
        
    await callback.message.edit_text(
        _("Awesome! Now select the specific Teams within those leagues you want to track predictions for:"),
        reply_markup=kb
    )
    await state.set_state(OnboardingStates.selecting_teams)

@router.callback_query(OnboardingStates.selecting_teams, F.data.startswith("toggle_team_"))
async def toggle_team_cb(callback: CallbackQuery, state: FSMContext):
    team_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = data.get('selected_teams', [])
    
    if team_id in selected:
        selected.remove(team_id)
    else:
        selected.append(team_id)
        
    await state.update_data(selected_teams=selected)
    
    async with AsyncSessionLocal() as session:
        kb = await render_teams_keyboard(session, data.get('selected_leagues', []), selected)
        
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@router.callback_query(OnboardingStates.selecting_teams, F.data == "teams_done")
async def teams_done_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_teams = data.get('selected_teams', [])
    squad_name = data.get('squad_name', 'My Squad')
    
    if not selected_teams:
        await callback.answer(_("Please select at least one team!"), show_alert=True)
        return
        
    user_id = callback.from_user.id
    invite_code = str(uuid.uuid4())[:8].upper()
    bot_username = (await callback.bot.me()).username
    invite_link = f"https://t.me/{bot_username}?start={invite_code}"
    
    async with AsyncSessionLocal() as session:
        new_squad = Squad(name=squad_name, admin_id=user_id, invite_code=invite_code, invite_link=invite_link)
        session.add(new_squad)
        await session.flush()
        
        member = SquadMember(user_id=user_id, squad_id=new_squad.id)
        session.add(member)
        
        for t_id in selected_teams:
            sq_team = SquadTeam(squad_id=new_squad.id, team_id=t_id)
            session.add(sq_team)
            
        await session.commit()
        
    await callback.message.edit_text(
        _("Squad '{squad_name}' created successfully! 🏆\n\n"
          "Your unique INVITATION CODE: `{invite_code}`\n"
          "Direct Telegram invite link: {invite_link}\n\n"
          "Share this code or link with your friends to invite them into the squad.").format(
              squad_name=squad_name, invite_code=invite_code, invite_link=invite_link
          ),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()
