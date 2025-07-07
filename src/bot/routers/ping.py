import enum
import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiohttp import ClientSession

from src.config import get_settings
from src.logger import logger

router = Router()
settings = get_settings()


class COMPONENTS(enum.StrEnum):
    app = "app"
    database = "database"
    redis_cache = "redis-cache"
    redis_blacklist = "redis-blacklist"
    httpx_client = "httpx-client"
    broker = "broker"


@router.message(Command("ping"))
async def handle_ping(message: Message):
    result = []

    async with ClientSession() as session:
        for component in COMPONENTS:
            result.append(await ping_component(component=component, session=session))

    await message.answer("\n\n".join(result))

    logger.debug(f"Ping command handled: from={message.from_user.username}")


async def ping_component(component: COMPONENTS, session: ClientSession):
    try:
        url = settings.PING_URL + str(component)
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            status = data.get("status")
            detail = data.get("detail")

            msg = f"{hbold(component)}: "
            if status == "ok":
                msg += f"✅ {status}"
            elif status == "error":
                msg += f"❌ {status}"
            else:
                msg += hbold("Not found")

            if detail:
                msg += f" ({detail})"

            return msg

    except Exception as e:
        logger.error(f"Failed to ping: component={component}, exception={repr(e)}")

        return f"Failed to ping {hbold(component)}: {html.escape(str(e), quote=False)}"


