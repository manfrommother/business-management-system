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

async def send_email_verification(email_to: str, token: str):
    '''Отправляет ссылку для подтерждения email'''
    verification_url = f'{settings.API_V1_STR}/verify-email?token={token}'

    message = MessageSchema(
        subject='Потверждение email',
        recipients=[email_to],
        template_body={
            'verification_url': verification_url
        },
        subtype='html'
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name='email_verification.html')
        return True
    except Exception as e:
        logging.error(f'Ошибка отправки emauk: {str(e)}')
        return False
    
async def send_password_reset(email_to: str, token: str):
    '''Отправка ссылки для сброса пароля'''
    reset_url = f'{settings.API_V1_STR}/reset-password?token={token}'

    message = MessageSchema(
        subject='Сброс пароля',
        recipients=[email_to],
        template_body={
            'reset_url': reset_url
        },
        subtype='html'
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name='password_reset.html')
        return True
    except Exception as e:
        logging.error(f'Ошибка отправки email для сброса пароля: {str(e)}')
        return False
    
async def send_account_deletion_notification(email_to: str, days_to_restore: int):
    '''Отправка уведомления об удалении аккаунта'''
    
    message = MessageSchema(
        subject='Уведомление об удалении аккаунта',
        recipients=[email_to],
        template_body={
            'days_to_restore': days_to_restore
        },
        subtype='html'
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name='account_deletion.html')
        return True
    except Exception as e:
        logging.error(f'Ошибка при отправке уведомления об удалении аккаунта: {str(e)}')
        return False