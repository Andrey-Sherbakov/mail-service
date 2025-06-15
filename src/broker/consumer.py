import asyncio
import json
import traceback
from dataclasses import dataclass
from typing import Callable, Awaitable

from aiokafka import AIOKafkaConsumer

from src.config import Settings


@dataclass
class BrokerConsumer:
    settings: Settings
    message_handler: Callable[[dict], Awaitable[None]]
    _consumer: AIOKafkaConsumer | None = None
    _consumer_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self.settings.BROKER_MAIL_TOPIC,
            bootstrap_servers=self.settings.BROKER_URL,
            group_id=self.settings.BROKER_GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self._consumer.start()
        self._consumer_task = asyncio.create_task(self._consume_loop())
        self._consumer_task.add_done_callback(self._handle_task_exception)

    async def stop(self) -> None:
        if self._consumer_task:
            self._consumer_task.cancel()
        if self._consumer:
            await self._consumer.stop()

    async def _consume_loop(self) -> None:
        try:
            async for message in self._consumer:
                await self.message_handler(message.value)
        except asyncio.CancelledError:
            pass

    @staticmethod
    def _handle_task_exception(task: asyncio.Task):
        if task.exception():
            raise task.exception()
