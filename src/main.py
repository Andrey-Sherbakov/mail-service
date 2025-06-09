from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.service import get_mail_service
from src.utils import broker_consumer_init, broker_connection_channel_init


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    publisher_connection, publisher_channel = await broker_connection_channel_init(
        settings=settings
    )
    consumer_connection, consumer_channel = await broker_connection_channel_init(settings=settings)

    mail_service = await get_mail_service(settings=settings, channel=publisher_channel)
    await broker_consumer_init(
        settings=settings, channel=consumer_channel, mail_service=mail_service
    )

    yield

    await publisher_channel.close()
    await publisher_connection.close()

    await consumer_channel.close()
    await consumer_connection.close()


app = FastAPI(lifespan=lifespan)
