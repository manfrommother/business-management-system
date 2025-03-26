import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import settings
from pathlib import Path
from typing import List

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_TLS=True,
    MAIL_SSL=False,
    TEMPLATE_FOLDER=Path(__file__).parent / "../templates/email"
)

logger = logging.getLogger(__name__)


async def send_team_invite(email_to: str, team_name: str, invite_code: str):
    """Отправка приглашения в команду"""
    # Формирование URL для присоединения к команде
    join_url = f"{settings.API_V1_STR}/teams/join?code={invite_code}"
    
    message = MessageSchema(
        subject=f"Приглашение в команду {team_name}",
        recipients=[email_to],
        template_body={
            "team_name": team_name,
            "join_url": join_url,
            "invite_code": invite_code
        },
        subtype="html"
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name="invite.html")
        logger.info(f"Отправлено приглашение в команду {team_name} на email {email_to}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки приглашения: {str(e)}")
        return False


async def send_team_news_notification(email_to: str, team_name: str, news_title: str, news_url: str):
    """Отправка уведомления о новой публикации в команде"""
    message = MessageSchema(
        subject=f"Новая публикация в команде {team_name}",
        recipients=[email_to],
        template_body={
            "team_name": team_name,
            "news_title": news_title,
            "news_url": news_url
        },
        subtype="html"
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name="news_notification.html")
        logger.info(f"Отправлено уведомление о новости {news_title} пользователю {email_to}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о новости: {str(e)}")
        return False


async def send_team_deleted_notification(email_to: str, team_name: str):
    """Отправка уведомления об удалении команды"""
    message = MessageSchema(
        subject=f"Команда {team_name} была удалена",
        recipients=[email_to],
        template_body={
            "team_name": team_name
        },
        subtype="html"
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name="team_deleted.html")
        logger.info(f"Отправлено уведомление об удалении команды {team_name} пользователю {email_to}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления об удалении команды: {str(e)}")
        return False