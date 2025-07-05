import asyncio
from dataclasses import dataclass

from aio_pika import Message as BrokerMessage
from aio_pika.abc import AbstractIncomingMessage
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from fastapi import FastAPI

from src.broker.producer import BrokerProducer
from src.config import Settings
from src.logger import logger


dp = Dispatcher()


@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer(text=f"Welcome to alarm bot!\nYour chat id is {message.chat.id}")
    logger.info(f"Start message handled: from={message.from_user.username}")


@dp.message()
async def handle_message(message: Message):
    await message.answer(text="I dont want to talk with you ...")
    logger.info(f"Message handled: message='{message.text}', from={message.from_user.username}")


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
