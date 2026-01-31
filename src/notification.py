"""通知モジュール．"""
import logging
import os

from discordwebhook import Discord

logger = logging.getLogger(__name__)


def send_discord_notification(message: str) -> bool:
    """Discordに通知を送信する．

    Args:
        message: 送信するメッセージ．

    Returns:
        送信成功の場合True．
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL not set, skipping notification")
        return False

    try:
        discord = Discord(url=webhook_url)
        discord.post(content=message)
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False
