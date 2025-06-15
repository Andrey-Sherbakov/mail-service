import json
from dataclasses import dataclass

from aiokafka import AIOKafkaProducer

from src.config import Settings


@dataclass
class BrokerProducer:
    settings: Settings
    _producer: AIOKafkaProducer | None = None

    async def send_mail(self, message: dict) -> None:
        await self._producer.send_and_wait(self.settings.BROKER_MAIL_CALLBACK_TOPIC, message)

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
