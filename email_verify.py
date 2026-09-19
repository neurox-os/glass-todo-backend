import os

from dotenv import load_dotenv

from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType
)

load_dotenv()


mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),

    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,

    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,

    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


fm = FastMail(mail_config)


async def send_verification_email(
    email: str,
    verification_code: str
) -> None:

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h2>Verify your email address</h2>

                <p>Thank you for signing up.</p>

                <p>Your verification code is:</p>

                <h1>{verification_code}</h1>

                <p>This code will expire in 5 minutes.</p>

                <p>
                    If you did not create this account,
                    you can ignore this email.
                </p>

                <p>
                    Thank You,<br>
                    Team Todo App
                </p>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )

    await fm.send_message(message)


async def send_reset_email(
    email: str,
    reset_code: str
) -> None:

    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>

                <p>Your password reset code is:</p>

                <h1>{reset_code}</h1>

                <p>This code will expire in 5 minutes.</p>

                <p>
                    If you did not request a password reset,
                    you can ignore this email.
                </p>

                <p>
                    Thank You,<br>
                    Team Todo App
                </p>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )

    await fm.send_message(message)