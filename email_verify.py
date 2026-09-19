import os
from dotenv import load_dotenv
from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
    MessageType
)

# Load environment variables
load_dotenv()

mail_username = os.getenv("MAIL_USERNAME")
mail_password = os.getenv("MAIL_PASSWORD")
mail_from = os.getenv("MAIL_FROM")
mail_from_name = os.getenv("MAIL_FROM_NAME")

# Group validation to raise a single error if multiple are missing
missing_vars = [
    var for var, val in {
        "MAIL_USERNAME": mail_username,
        "MAIL_PASSWORD": mail_password,
        "MAIL_FROM": mail_from,
        "MAIL_FROM_NAME": mail_from_name
    }.items() if not val
]

if missing_vars:
    raise RuntimeError(f"Missing required email configuration: {', '.join(missing_vars)}")

# Configure FastMail for Gmail
mail_config = ConnectionConfig(
    MAIL_USERNAME=mail_username,
    MAIL_PASSWORD=mail_password,
    MAIL_FROM=mail_from,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME=mail_from_name,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(mail_config)

async def send_verification_email(email: str, verification_code: str) -> None:
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
                <p>If you did not create this account, you can ignore this email.</p>
                <p>Thank You,<br>Team Todo App</p>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )
    await fm.send_message(message)

async def send_reset_email(email: str, reset_code: str) -> None:
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"""
        <html>
            <body>
                <h2>Password reset request</h2>
                <p>Your password reset code is:</p>
                <h1>{reset_code}</h1>
                <p>This code will expire in 5 minutes.</p>
                <p>If you did not request a password reset, you can ignore this email.</p>
                <p>Thank You,<br>Team Todo App</p>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )
    await fm.send_message(message)