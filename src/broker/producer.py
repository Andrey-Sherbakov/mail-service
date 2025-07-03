from dataclasses import dataclass

import aio_pika
from aio_pika.abc import (
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractQueue,
    AbstractMessage,
)
from fastapi import FastAPI

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
            message=message, routing_key=self.settings.BROKER_CALLBACK_TOPIC
        )
        logger.debug("Callback message published")

    async def start(self):
        self._connection = await aio_pika.connect_robust(self.settings.BROKER_URL)
        self._channel = await self._connection.channel()
        self._queue = await self._channel.declare_queue(
            self.settings.BROKER_CALLBACK_TOPIC, durable=True
        )
        logger.debug("Broker producer started")

    async def stop(self):
        await self._channel.close()
        await self._connection.close()
        logger.debug("Broker producer stopped")


async def producer_startup(app: FastAPI, settings: Settings):
    broker_producer = BrokerProducer(settings=settings)
    app.state.broker_producer = broker_producer
    await broker_producer.start()


async def producer_shutdown(app: FastAPI):
    await app.state.broker_producer.stop()
