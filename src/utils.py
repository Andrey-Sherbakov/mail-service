import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from src.config import Settings
from src.service import MailService


async def broker_connection_channel_init(
    settings: Settings,
) -> tuple[AbstractRobustConnection, AbstractRobustChannel]:
    connection = await aio_pika.connect_robust(settings.BROKER_URL)
    channel = await connection.channel()
    return connection, channel


async def broker_consumer_init(
    settings: Settings, channel: AbstractRobustChannel, mail_service: MailService
) -> None:
    queue = await channel.declare_queue(settings.BROKER_MAIL_ROUTING_KEY, durable=True)

    await queue.consume(mail_service.consume_message)
