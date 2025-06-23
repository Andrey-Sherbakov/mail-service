import asyncio
import json
from dataclasses import dataclass
from typing import Callable, Awaitable

import aio_pika
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractQueue,
)

from src.config import Settings


@dataclass
class BrokerConsumer:
    settings: Settings
    message_handler: Callable[[AbstractIncomingMessage], Awaitable[None]] | None = None
    _connection: AbstractRobustConnection | None = None
    _channel: AbstractRobustChannel | None = None
    _queue: AbstractQueue | None = None

    async def start(self):
        self._connection = await aio_pika.connect_robust(self.settings.BROKER_URL)
        self._channel = await self._connection.channel()
        self._queue = await self._channel.declare_queue(
            self.settings.BROKER_MAIL_TOPIC, durable=True
        )

    async def stop(self):
        await self._channel.close()
        await self._connection.close()

    async def consume(self):
        handler = self.default_message_handler
        if self.message_handler:
            handler = self.message_handler

        await self._queue.consume(handler)

    @staticmethod
    async def default_message_handler(message: AbstractIncomingMessage):
        async with message.process():
            body = message.body.decode()
            correlation_id = message.correlation_id
            print(body, correlation_id)
