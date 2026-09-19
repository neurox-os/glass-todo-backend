import os

import resend
from dotenv import load_dotenv

load_dotenv()

resend_api_key = os.getenv("RESEND_API_KEY")
mail_from = os.getenv("MAIL_FROM")

missing_vars = [
    var
    for var, val in {
        "RESEND_API_KEY": resend_api_key,
        "MAIL_FROM": mail_from,
    }.items()
    if not val
]

if missing_vars:
    raise RuntimeError(
        f"Missing required email configuration: {', '.join(missing_vars)}"
    )

resend.api_key = resend_api_key


async def send_verification_email(
    email: str,
    verification_code: str
) -> None:

    params = {
        "from": mail_from,
        "to": [email],
        "subject": "Verify your email",
        "html": f"""
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
        """
    }

    resend.Emails.send(params)


async def send_reset_email(
    email: str,
    reset_code: str
) -> None:

    params = {
        "from": mail_from,
        "to": [email],
        "subject": "Reset your password",
        "html": f"""
        <html>
            <body>
                <h2>Password reset request</h2>

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
        """
    }

    resend.Emails.send(params)