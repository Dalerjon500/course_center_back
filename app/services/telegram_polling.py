from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class TelegramPollingRunner:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()
        self._offset = 0
        self._conflict_logged = False

    def should_run(self) -> bool:
        return bool(settings.TELEGRAM_USE_POLLING and settings.TELEGRAM_BOT_TOKEN)

    async def start(self) -> None:
        if not self.should_run() or self._task is not None:
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run(), name="telegram-polling-runner")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
        delete_webhook_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteWebhook"
        async with httpx.AsyncClient(timeout=35.0) as client:
            await self._delete_webhook(client, delete_webhook_url)
            while not self._stopped.is_set():
                try:
                    response = await client.get(
                        api_url,
                        params={"timeout": 25, "offset": self._offset},
                    )
                    if response.status_code == 409:
                        await self._handle_conflict(response)
                        continue
                    response.raise_for_status()
                    self._conflict_logged = False
                    payload = response.json()
                    for update in payload.get("result", []):
                        update_id = update.get("update_id")
                        if isinstance(update_id, int):
                            self._offset = max(self._offset, update_id + 1)
                        await asyncio.to_thread(self._process_update, update)
                except asyncio.CancelledError:
                    raise
                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code
                    logger.warning("Telegram polling request failed with HTTP %s", status_code)
                    await asyncio.sleep(3)
                except httpx.HTTPError as exc:
                    logger.warning("Telegram polling request failed: %s", exc.__class__.__name__)
                    await asyncio.sleep(3)
                except Exception as exc:
                    logger.exception("Telegram polling failed: %s", exc)
                    await asyncio.sleep(3)

    async def _delete_webhook(self, client: httpx.AsyncClient, delete_webhook_url: str) -> None:
        try:
            response = await client.post(delete_webhook_url)
            response.raise_for_status()
            payload = response.json()
            if payload.get("ok"):
                logger.info("Telegram webhook cleared before polling startup")
            else:
                logger.warning(
                    "Telegram webhook cleanup was not accepted: %s",
                    payload.get("description", "unknown Telegram response"),
                )
        except httpx.HTTPError as exc:
            logger.warning("Telegram webhook cleanup failed: %s", exc.__class__.__name__)

    async def _handle_conflict(self, response: httpx.Response) -> None:
        description = "another getUpdates request or webhook is active"
        try:
            description = response.json().get("description") or description
        except ValueError:
            pass

        if not self._conflict_logged:
            logger.warning(
                "Telegram polling conflict: %s. Stop other bot instances or disable TELEGRAM_USE_POLLING there.",
                description,
            )
            self._conflict_logged = True
        await asyncio.sleep(30)

    @staticmethod
    def _process_update(update: dict) -> None:
        db = SessionLocal()
        try:
            TelegramService(db).handle_webhook(update)
        finally:
            db.close()


telegram_polling_runner = TelegramPollingRunner()
