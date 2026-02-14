"""Email service for SMTP sending and IMAP reading."""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from uuid import UUID

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_value, decrypt_value
from app.models.email_config import EmailConfig

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, db: AsyncSession | None):
        self.db = db

    async def get_config(self, user_id: str) -> EmailConfig | None:
        if not self.db:
            return None
        stmt = select(EmailConfig).where(
            EmailConfig.user_id == UUID(user_id), EmailConfig.is_active == True
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def send_email(
        self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str,
        to: str, subject: str, body: str, reply_to: str | None = None,
    ) -> dict:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to
            msg["Subject"] = subject
            if reply_to:
                msg["In-Reply-To"] = reply_to
            msg.attach(MIMEText(body, "plain", "utf-8"))

            async with aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port, use_tls=False, start_tls=True) as client:
                await client.login(smtp_user, smtp_password)
                await client.send_message(msg)

            return {"success": True, "to": to, "subject": subject}
        except Exception as e:
            logger.error("SMTP send failed: %s", e)
            return {"success": False, "error": str(e)}

    async def read_emails(
        self, imap_host: str, imap_port: int, imap_user: str, imap_password: str,
        folder: str = "INBOX", limit: int = 10,
    ) -> dict:
        try:
            import aioimaplib
            client = aioimaplib.IMAP4_SSL(host=imap_host, port=imap_port)
            await client.wait_hello_from_server()
            await client.login(imap_user, imap_password)
            await client.select(folder)
            _, data = await client.search("ALL")
            message_ids = data[0].split()[-limit:]
            emails = []
            for msg_id in message_ids:
                _, msg_data = await client.fetch(msg_id.decode(), "(RFC822)")
                if msg_data:
                    emails.append({"id": msg_id.decode(), "raw": str(msg_data)[:500]})
            await client.logout()
            return {"success": True, "count": len(emails), "emails": emails}
        except Exception as e:
            logger.error("IMAP read failed: %s", e)
            return {"success": False, "error": str(e)}

    async def save_config(
        self, user_id: str, smtp_host: str, smtp_port: int, smtp_user: str,
        smtp_password: str, imap_host: str, imap_port: int, imap_user: str, imap_password: str,
    ) -> EmailConfig:
        existing = await self.get_config(user_id)
        if existing:
            existing.smtp_host = smtp_host
            existing.smtp_port = smtp_port
            existing.smtp_user = smtp_user
            existing.smtp_password_encrypted = encrypt_value(smtp_password)
            existing.imap_host = imap_host
            existing.imap_port = imap_port
            existing.imap_user = imap_user
            existing.imap_password_encrypted = encrypt_value(imap_password)
            await self.db.flush()
            return existing

        config = EmailConfig(
            user_id=UUID(user_id), smtp_host=smtp_host, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password_encrypted=encrypt_value(smtp_password),
            imap_host=imap_host, imap_port=imap_port, imap_user=imap_user,
            imap_password_encrypted=encrypt_value(imap_password), is_active=True,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config
