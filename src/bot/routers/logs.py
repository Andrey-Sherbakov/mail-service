import os
import html
from collections import deque

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from src.logger import logger

router = Router()

NAME_MAP = {"1": "pomodoro-time", "2": "mail-service"}
LEVEL_MAP = {"1": "debug", "2": "info", "3": "warning"}


class LogQuery(StatesGroup):
    waiting_name_level = State()


@router.message(Command("logs"))
async def handle_logs(message: Message, state: FSMContext):
    await message.answer(
        "Приложение для логов:\n1)pomodoro-time\n2)mail-service\n"
        "Уровень логирования:\n1)debug\n2)info\n3)warning\n"
        "Данные введите через пробел:"
    )
    await state.set_state(LogQuery.waiting_name_level)

    logger.debug(f"Logs command handled: from={message.from_user.username}")


@router.message(LogQuery.waiting_name_level)
async def handle_logs_name_level_state(message: Message, state: FSMContext):
    log_name_level = message.text.strip().split()
    if (
        len(log_name_level) != 2
        or log_name_level[0] not in ["1", "2"]
        or log_name_level[1] not in ["1", "2", "3"]
    ):
        await message.answer("Неверные входные данные!")
        await state.clear()

        logger.debug(
            f"Logs name-level-state handled: status=failure, "
            f"message={message.text}, from={message.from_user.username}"
        )

        return

    app_name = NAME_MAP.get(log_name_level[0], NAME_MAP["1"])
    log_level = LEVEL_MAP.get(log_name_level[1], LEVEL_MAP["2"])

    file_path = f"../logs/{app_name}/{log_level}.log"

    if not os.path.isfile(file_path):
        await message.answer(f"Файл логов не найден по пути: {file_path}")
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            last_lines = list(deque(f, maxlen=10))
            response = "\n".join(last_lines)
            await message.answer(
                text=f"Последние логи из `{hbold(app_name)}` уровня `{hbold(log_level)}`:\n\n"
                f"{html.escape(response, quote=False)}"
            )

    await state.clear()

    logger.debug(
        f"Logs name-level-state handled: status=success, "
        f"message={message.text}, from={message.from_user.username}"
    )
