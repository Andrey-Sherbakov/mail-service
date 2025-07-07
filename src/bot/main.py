import asyncio
from dataclasses import dataclass

from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI

from src.broker.producer import BrokerProducer
from src.config import Settings
from src.logger import logger
from src.bot.routers import default_router, logs_router, ping_router


@dataclass
class TelegramBot:
    routers: list[Router]
    settings: Settings
    producer: BrokerProducer
    _bot: Bot | None = None
    _dp: Dispatcher | None = None
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

        callback_message = Message(
            body="Telegram message successfully send".encode(),
            correlation_id=correlation_id,
        )
        await self.producer.publish(message=callback_message)

    async def start(self):
        self._bot = Bot(
            self.settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self._dp = Dispatcher(storage=MemoryStorage())

        for router in self.routers:
            self._dp.include_router(router)

        self._tg_task = asyncio.create_task(self._dp.start_polling(self._bot))

        logger.debug("Telegram bot started")

    async def stop(self):
        await self._bot.session.close()
        self._tg_task.cancel()

        logger.debug("Telegram bot stopped")


async def bot_startup(app: FastAPI):
    routers = [
        logs_router,
        ping_router,
        default_router,
    ]
    bot = TelegramBot(
        routers=routers, settings=app.state.settings, producer=app.state.broker_producer
    )
    await bot.start()
    app.state.bot = bot


async def bot_shutdown(app: FastAPI):
    await app.state.bot.stop()
