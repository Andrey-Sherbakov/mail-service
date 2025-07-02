from dataclasses import dataclass

import aio_pika
from aio_pika.abc import (
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractQueue,
    AbstractMessage,
)

from src.config import Settings
from src.logger import logger


@dataclass
class BrokerProducer:
    settings: Settings
    _connection: AbstractRobustConnection | None = None
    _channel: AbstractRobustChannel | None = None
    _queue: AbstractQueue | None = None

    async def publish(self, message: AbstractMessage):
        await self._channel.default_exchange.publish(
            message=message, routing_key=self.settings.BROKER_MAIL_CALLBACK_TOPIC
        )
        logger.debug("Callback message published")

    async def start(self):
        self._connection = await aio_pika.connect_robust(self.settings.BROKER_URL)
        self._channel = await self._connection.channel()
        self._queue = await self._channel.declare_queue(
            self.settings.BROKER_MAIL_CALLBACK_TOPIC, durable=True
        )
        logger.debug("Broker producer started")

    async def stop(self):
        await self._channel.close()
        await self._connection.close()
        logger.debug("Broker producer stopped")
