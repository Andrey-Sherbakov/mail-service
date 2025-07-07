from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.logger import logger

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message):
    await message.answer(
        text=f"Welcome to alarm bot!\nYour chat id is\n - {message.chat.id}\n"
        f"Available commands:\n - /start\n - /logs\n - /ping"
    )
    logger.debug(f"Start command handled: from={message.from_user.username}")


@router.message()
async def handle_default_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(text="Available commands:\n - /start\n - /logs\n - /ping")
        logger.debug(
            f"Message handled: message='{message.text}', from={message.from_user.username}"
        )
    else:
        logger.warning("Default message handler with active state!")