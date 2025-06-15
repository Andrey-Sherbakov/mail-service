from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.broker.consumer import BrokerConsumer
from src.broker.producer import BrokerProducer
from src.config import get_settings
from src.service import get_mail_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    broker_producer = BrokerProducer(settings=settings)
    app.state.broker_producer = broker_producer
    await broker_producer.start()

    mail_service = await get_mail_service(settings=settings, broker_producer=broker_producer)
    broker_consumer = BrokerConsumer(
        settings=settings, message_handler=mail_service.consume_message
    )
    app.state.broker_consumer = broker_consumer
    await broker_consumer.start()

    yield

    await app.state.broker_producer.stop()
    await app.state.broker_consumer.stop()


app = FastAPI(lifespan=lifespan)
