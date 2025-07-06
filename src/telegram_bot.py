import asyncio
import os
from collections import deque
from dataclasses import dataclass

from aio_pika import Message as BrokerMessage
from aio_pika.abc import AbstractIncomingMessage
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import Command
from fastapi import FastAPI

from src.broker.producer import BrokerProducer
from src.config import Settings
from src.logger import logger


dp = Dispatcher(storage=MemoryStorage())


@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer(
        text=f"Welcome to alarm bot!\nYour chat id is\n - {message.chat.id}\n"
        f"Available commands:\n - /start\n - /logs"
    )
    logger.info(f"Start message handled: from={message.from_user.username}")


#### эксперимент
class LogQuery(StatesGroup):
    waiting_for_app_name_and_level = State()


@dp.message(Command("logs"))
async def cmd_logs(message: Message, state: FSMContext):
    await message.answer(
        "Приложение для логов:\n1)pomodoro-time\n2)mail-service\n"
        "Уровень логирования:\n1)debug\n2)info\n3)warning\n"
        "Данные введите через пробел:"
    )
    await state.set_state(LogQuery.waiting_for_app_name_and_level)


@dp.message(LogQuery.waiting_for_app_name_and_level)
async def log_level_entered(message: Message, state: FSMContext):
    name_map = {"1": "pomodoro-time", "2": "mail-service"}
    level_map = {"1": "debug", "2": "info", "3": "warning"}

    log_name_level = message.text.strip().split()
    if (
        len(log_name_level) != 2
        or log_name_level[0] not in ["1", "2"]
        or log_name_level[1] not in ["1", "2", "3"]
    ):
        await message.answer("Неверные входные данные!")
        await state.clear()
        return

    app_name = name_map.get(log_name_level[0], name_map["1"])
    log_level = level_map.get(log_name_level[1], level_map["2"])

    file_path = f"../logs/{app_name}/{log_level}.log"

    if not os.path.isfile(file_path):
        await message.answer(f"Файл логов не найден по пути: {file_path}")
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            last_lines = list(deque(f, maxlen=10))
            response = "\n".join(last_lines)
            await message.answer(
                text=f"Последние логи из `{app_name}` уровня `{log_level}`:\n\n{response}"
            )

    await state.clear()


######


@dp.message()
async def handle_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(text="Available commands:\n - /start\n - /logs")
        logger.info(f"Message handled: message='{message.text}', from={message.from_user.username}")
    else:
        logger.warning("Default message handler with active state!")


@dataclass
class TelegramBot:
    settings: Settings
    dp: Dispatcher
    producer: BrokerProducer
    _bot: Bot | None = None
    _tg_task: asyncio.Task | None = None

    async def send_message(self, message: str, chat_id: int | None = None):
        if chat_id is None:
            chat_id = self.settings.CHAT_ID

        await self._bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Telegram message send: message='{message}', to={chat_id}")

    async def broker_message_handler(self, message: AbstractIncomingMessage):
        async with message.process():
            body = message.body.decode()
            correlation_id = message.correlation_id
        await self.send_message(message=body)

        callback_message = BrokerMessage(
            body="Telegram message successfully send".encode(),
            correlation_id=correlation_id,
        )
        await self.producer.publish(message=callback_message)

    async def start(self):
        self._bot = Bot(self.settings.BOT_TOKEN)
        self._tg_task = asyncio.create_task(self._polling())

        logger.debug("Telegram bot started")

    async def stop(self):
        await self._bot.session.close()
        self._tg_task.cancel()

        logger.debug("Telegram bot stopped")

    async def _polling(self):
        logger.debug("Telegram bot polling ...")

        await self.dp.start_polling(self._bot)


async def bot_startup(app: FastAPI):
    bot = TelegramBot(settings=app.state.settings, dp=dp, producer=app.state.broker_producer)
    await bot.start()
    app.state.bot = bot


async def bot_shutdown(app: FastAPI):
    await app.state.bot.stop()
