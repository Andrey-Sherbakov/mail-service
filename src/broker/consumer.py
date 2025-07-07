from dataclasses import dataclass
from typing import Callable, Awaitable

import aio_pika
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractQueue,
)
from fastapi import FastAPI

from src.config import Settings
from src.logger import logger


@dataclass
class BrokerConsumer:
    settings: Settings
    mail_handler: Callable[[AbstractIncomingMessage], Awaitable[None]]
    tg_handler: Callable[[AbstractIncomingMessage], Awaitable[None]]
    _connection: AbstractRobustConnection | None = None
    _channel: AbstractRobustChannel | None = None
    _mail_queue: AbstractQueue | None = None
    _tg_queue: AbstractQueue | None = None

    async def start(self):
        self._connection = await aio_pika.connect_robust(self.settings.BROKER_URL)
        self._channel = await self._connection.channel()
        self._mail_queue = await self._channel.declare_queue(
            self.settings.BROKER_MAIL_TOPIC, durable=True
        )
        self._tg_queue = await self._channel.declare_queue(
            self.settings.BROKER_TG_TOPIC, durable=True
        )
        logger.debug("Broker consumer started")

    async def stop(self):
        await self._channel.close()
        await self._connection.close()
        logger.debug("Broker consumer stopped")

    async def consume(self):
        await self._mail_queue.consume(self.mail_handler)
        await self._tg_queue.consume(self.tg_handler)
        logger.debug("Broker cunsuming ...")

    @staticmethod
    async def default_message_handler(message: AbstractIncomingMessage):
        async with message.process():
            body = message.body.decode()
            correlation_id = message.correlation_id
            logger.info(f"Message recieved: body={body}, correlation_id={correlation_id}")


async def consumer_startup(app: FastAPI):
    broker_consumer = BrokerConsumer(
        settings=app.state.settings,
        mail_handler=app.state.mail_service.consume_message,
        tg_handler=app.state.bot.broker_message_handler,
    )
    app.state.broker_consumer = broker_consumer
    await broker_consumer.start()
    await broker_consumer.consume()


async def consumer_shutdown(app: FastAPI):
    await app.state.broker_consumer.stop()
