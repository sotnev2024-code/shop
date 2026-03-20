import asyncio
import logging
from typing import Optional, List, Union

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from app.db.session import async_session
from app.db.models.user import User
from app.db.models.product import Product
from app.services.try_on_service import try_on_service
from app.services.post_service import _absolute_photo_url
from app.config import settings
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

router = Router()

class TryOnStates(StatesGroup):
    selecting_product_image = State()
    waiting_for_user_photo = State()

def _absolute_url(url: str) -> str:
    """Imported from post_service for consistency."""
    return _absolute_photo_url(url)

@router.callback_query(F.data.startswith("check_sub:"))
async def handle_check_sub(callback: CallbackQuery, state: FSMContext):
    """Verify subscription and grant bonus attempts."""
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    if not settings.channel_id:
        await callback.answer("Настройка подписки отключена.")
        return await handle_try_on_logic(callback, product_id, state)

    try:
        member = await callback.bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
        is_subscribed = member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        is_subscribed = False

    if is_subscribed:
        async with async_session() as db:
            result = await db.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            if user and not user.try_on_bonus_received:
                user.try_on_attempts += 3
                user.try_on_bonus_received = True
                await db.commit()
                await callback.message.answer("Подписка подтверждена! Вам начислено **3 бесплатные примерки** ✨", parse_mode="Markdown")
        
        await callback.answer("Подписка подтверждена!")
        await handle_try_on_logic(callback, product_id, state)
    else:
        await callback.answer("Вы всё еще не подписаны на канал 😔", show_alert=True)

@router.message(Command("try_it_on"))
async def cmd_try_it_on(message: Message):
    """Handle /try_it_on command."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                try_on_attempts=0,
                try_on_bonus_received=False
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Check if they can get bonus by subscribing
        if settings.channel_id and not user.try_on_bonus_received:
            try:
                member = await message.bot.get_chat_member(chat_id=settings.channel_id, user_id=message.from_user.id)
                is_subscribed = member.status in ["member", "administrator", "creator"]
            except Exception:
                is_subscribed = False

            if not is_subscribed:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{settings.channel_id.replace('@', '')}")],
                    [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub_only")]
                ])
                await message.answer(
                    "У вас пока нет доступных примерок. 😔\n\n"
                    "Подпишитесь на наш канал и получите **3 бесплатные примерки**! ✨",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            else:
                # Subscribed but bonus not yet recorded
                user.try_on_attempts += 3
                user.try_on_bonus_received = True
                await db.commit()
                await message.answer("Спасибо за подписку! Вам начислено **3 бесплатные примерки** ✨", parse_mode="Markdown")

        if user.try_on_attempts <= 0:
            await message.answer(
                f"У вас 0 доступных примерок. 😔\n\n"
                "Вы можете пополнить баланс с помощью команды /pay"
            )
            return
            
        await message.answer(
            f"У вас осталось {user.try_on_attempts} примерок. ✨\n\n"
            "Чтобы примерить товар, перейдите в каталог в приложении и нажмите кнопку 'Примерить' на карточке товара."
        )

@router.callback_query(F.data == "check_sub_only")
async def handle_check_sub_only(callback: CallbackQuery):
    """Verify subscription from /try_it_on command without product_id."""
    user_id = callback.from_user.id
    if not settings.channel_id:
        await callback.answer("Настройка подписки отключена.")
        return

    try:
        member = await callback.bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
        is_subscribed = member.status in ["member", "administrator", "creator"]
    except Exception:
        is_subscribed = False

    if is_subscribed:
        async with async_session() as db:
            result = await db.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            if user and not user.try_on_bonus_received:
                user.try_on_attempts += 3
                user.try_on_bonus_received = True
                await db.commit()
                await callback.message.answer("Подписка подтверждена! Вам начислено **3 бесплатные примерки** ✨", parse_mode="Markdown")
        
        await callback.answer("Подписка подтверждена!")
        await cmd_try_it_on(callback.message)
    else:
        await callback.answer("Вы всё еще не подписаны на канал 😔", show_alert=True)

@router.callback_query(F.data.startswith("try_it_on:"))
async def handle_try_on_callback(callback: CallbackQuery, state: FSMContext):
    """Handle 'Try it on' button click."""
    product_id = int(callback.data.split(":")[1])
    await handle_try_on_logic(callback, product_id, state)

async def handle_try_on_logic(event: Union[Message, CallbackQuery], product_id: int, state: FSMContext):
    """Start try-on flow from either a button click (CallbackQuery) or deep link (Message)."""
    user_id = event.from_user.id
    message = event if isinstance(event, Message) else event.message
    
    async with async_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=user_id,
                first_name=event.from_user.first_name,
                last_name=event.from_user.last_name,
                username=event.from_user.username,
                try_on_attempts=0,
                try_on_bonus_received=False
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # 1. Check if subscription is required and not yet verified
        if settings.channel_id:
            try:
                member = await event.bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
                is_subscribed = member.status in ["member", "administrator", "creator"]
            except Exception as e:
                logger.error(f"Error checking channel membership: {e}")
                is_subscribed = False # Assume not subscribed on error for safety

            if not is_subscribed:
                # If not subscribed, check if they can get bonus later
                channel_link = settings.channel_id if settings.channel_id.startswith("@") else f"t.me/{settings.channel_id.replace('-100', '')}"
                if not channel_link.startswith("t.me"):
                    # Try to get invite link if it's a private channel, but here we'll just assume @username or public
                    pass
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{settings.channel_id.replace('@', '')}")],
                    [InlineKeyboardButton(text="✅ Проверить подписку", callback_data=f"check_sub:{product_id}")]
                ])
                
                await message.answer(
                    "Чтобы воспользоваться функцией примерки, необходимо подписаться на наш канал! 📢\n\n"
                    "После подписки вы получите **3 бесплатные примерки** ✨",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            
            # If subscribed but hasn't received bonus yet
            if not user.try_on_bonus_received:
                user.try_on_attempts += 3
                user.try_on_bonus_received = True
                await db.commit()
                await message.answer("Спасибо за подписку! Вам начислено **3 бесплатные примерки** ✨", parse_mode="Markdown")

        if user.try_on_attempts <= 0:
            await message.answer(
                "У вас закончились бесплатные примерки. 😔\n\n"
                "Вы можете пополнить баланс с помощью команды /pay"
            )
            return

        # Fetch product with media
        result = await db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.media))
        )
        product = result.scalar_one_or_none()
        
        if not product:
            if isinstance(event, CallbackQuery):
                await event.answer("Товар не найден.", show_alert=True)
            else:
                await event.answer("Товар не найден.")
            return
            
        # Collect all image URLs and make them absolute
        images = []
        if product.media:
            images = [_absolute_url(m.file_path) for m in sorted(product.media, key=lambda x: x.sort_order) if m.media_type == "image"]
        if not images and product.image_url:
            images = [_absolute_url(product.image_url)]
            
        if not images:
            if isinstance(event, CallbackQuery):
                await event.answer("У этого товара нет изображений для примерки.", show_alert=True)
            else:
                await event.answer("У этого товара нет изображений для примерки.")
            return

        if isinstance(event, CallbackQuery):
            await event.answer()
        
        # Start selection flow
        await state.update_data(product_id=product_id, product_images=images, current_image_idx=0)
        await show_image_selection(message, images[0], 0, len(images), state)
        await state.set_state(TryOnStates.selecting_product_image)

async def show_image_selection(message: Message, image_url: str, idx: int, total: int, state: FSMContext):
    """Show product image with navigation buttons."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"try_on_prev:{idx}"),
            InlineKeyboardButton(text=f"{idx + 1}/{total}", callback_data="none"),
            InlineKeyboardButton(text="➡️", callback_data=f"try_on_next:{idx}"),
        ],
        [InlineKeyboardButton(text="✅ Выбрать это фото", callback_data=f"try_on_select:{idx}")]
    ])
    
    # Try to use answer_photo if it's not an update to an existing photo message
    try:
        if message.photo:
            await message.edit_media(
                media=types.InputMediaPhoto(media=image_url, caption="Выберите фотографию товара для примерки:"),
                reply_markup=keyboard
            )
        else:
            await message.answer_photo(
                photo=image_url,
                caption="Выберите фотографию товара для примерки:",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.warning(f"Failed to show image at index {idx}: {e}")
        # Mark this image as broken by removing it from the list in state
        data = await state.get_data()
        images = list(data.get("product_images", []))
        
        if idx < len(images):
            images.pop(idx)
            await state.update_data(product_images=images)
            
            if not images:
                await message.answer("К сожалению, не удалось загрузить ни одного изображения товара для примерки. 😔")
                await state.clear()
                return

            # Try to show the next available image (or the first one if we were at the end)
            new_idx = idx % len(images)
            await state.update_data(current_image_idx=new_idx)
            await show_image_selection(message, images[new_idx], new_idx, len(images), state)
        else:
            # Fallback if indices are messed up
            await message.answer("Произошла ошибка при загрузке изображений товара. Попробуйте выбрать другой товар.")
            await state.clear()

@router.callback_query(F.data.startswith("try_on_prev:"))
async def handle_prev_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    images = data.get("product_images", [])
    if not images:
        await callback.answer("Нет доступных изображений.")
        return

    current_idx = int(callback.data.split(":")[1])
    new_idx = (current_idx - 1) % len(images)
    
    await state.update_data(current_image_idx=new_idx)
    await show_image_selection(callback.message, images[new_idx], new_idx, len(images), state)
    await callback.answer()

@router.callback_query(F.data.startswith("try_on_next:"))
async def handle_next_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    images = data.get("product_images", [])
    if not images:
        await callback.answer("Нет доступных изображений.")
        return

    current_idx = int(callback.data.split(":")[1])
    new_idx = (current_idx + 1) % len(images)
    
    await state.update_data(current_image_idx=new_idx)
    await show_image_selection(callback.message, images[new_idx], new_idx, len(images), state)
    await callback.answer()

@router.callback_query(F.data.startswith("try_on_select:"))
async def handle_select_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    images = data.get("product_images", [])
    idx = int(callback.data.split(":")[1])
    selected_image = images[idx]
    
    await state.update_data(selected_product_image=selected_image)
    await state.set_state(TryOnStates.waiting_for_user_photo)
    
    await callback.message.answer(
        "Отлично! Теперь пришлите вашу фотографию. 📸\n\n"
        "Инструкция: вы должны быть на фото хотя бы наполовину, начиная с торса. "
        "Желательно хорошее освещение и однотонный фон."
    )
    await callback.answer()

@router.message(TryOnStates.waiting_for_user_photo, F.photo)
async def handle_user_photo(message: Message, state: FSMContext):
    """Handle user photo and start generation."""
    photo = message.photo[-1] # Highest resolution
    file = await message.bot.get_file(photo.file_id)
    # Build URL for Telegram photo (note: this URL is temporary, usually lasts ~1h)
    user_photo_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file.file_path}"
    
    data = await state.get_data()
    product_image_url = data.get("selected_product_image")
    
    if not product_image_url:
        await message.answer("Произошла ошибка (не выбрано фото товара). Попробуйте снова.")
        await state.clear()
        return

    # Deduction of attempts
    async with async_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user or user.try_on_attempts <= 0:
            await message.answer("У вас закончились попытки примерки.")
            await state.clear()
            return
            
        user.try_on_attempts -= 1
        await db.commit()
        remaining = user.try_on_attempts

    msg = await message.answer(f"Начинаю генерацию... 🚀\n(Осталось примерок: {remaining})")
    
    # Start generation in background or just wait here if it's not too long
    # Since we want to provide the result, we'll wait or use a task
    
    try:
        # Prompt for virtual try-on
        prompt = "Virtual try-on: person wearing the provided garment. Maintain the person's features and the garment's design."
        
        task_id = await try_on_service.create_generation_task(
            prompt=prompt,
            image_urls=[user_photo_url, _absolute_url(product_image_url)]
        )
        
        if not task_id:
            await msg.edit_text("К сожалению, не удалось создать задачу генерации. Попробуйте позже.")
            # Refund attempt? User might want that
            async with async_session() as db:
                result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
                user = result.scalar_one_or_none()
                if user:
                    user.try_on_attempts += 1
                    await db.commit()
            return

        # Wait for result
        result_urls = await try_on_service.wait_for_result(task_id)
        
        if result_urls:
            await message.answer_photo(
                photo=result_urls[0],
                caption="Ваша примерка готова! ✨"
            )
            await msg.delete()
        else:
            await msg.edit_text("Произошла ошибка при генерации. Попробуйте позже.")
            # Refund
            async with async_session() as db:
                result = await db.execute(select(User).where(User.telegram_id == message.from_user.id))
                user = result.scalar_one_or_none()
                if user:
                    user.try_on_attempts += 1
                    await db.commit()

    except Exception as e:
        logger.error(f"Try-on error: {e}", exc_info=True)
        await msg.edit_text("Произошла непредвиденная ошибка. Попробуйте позже.")
    
    await state.clear()
