from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.broker.consumer import consumer_startup, consumer_shutdown
from src.broker.producer import producer_startup, producer_shutdown
from src.config import get_settings
from src.service import setup_mail_service
from src.telegram_bot import TelegramBot, bot_startup, bot_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()

    await producer_startup(app=app)
    await setup_mail_service(app=app)
    await bot_startup(app=app)
    await consumer_startup(app=app)

    yield

    await producer_shutdown(app)
    await consumer_shutdown(app)
    await bot_shutdown(app)


app = FastAPI(lifespan=lifespan)


@app.post("/send-tg-message")
async def send_message_with_telegram(message: str):
    bot: TelegramBot = app.state.bot
    await bot.send_message(message=message)
    return {"detail": "Message send"}
