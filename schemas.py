from pydantic import BaseModel, EmailStr, Field, ConfigDict

class NewUser(BaseModel):

    username: str = Field(
        ...,
        min_length=5,
        max_length=32,
        description="Username"
    )

    email: EmailStr = Field(
        ...,
        description="Email address"
    )

    password: str = Field(
        ...,
        min_length=8,
        description="Password"
    )

class Token(BaseModel):

    access_token: str

    token_type: str

class VerifyEmail(BaseModel):

    verification_id: str = Field(
        ...,
        min_length=1
    )

    code: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="6-digit verification code"
    )

class ChangePassword(BaseModel):

    old_password: str = Field(
        ...,
        min_length=1
    )

    new_password: str = Field(
        ...,
        min_length=8
    )

class VerifyCode(BaseModel):

    reset_id: str = Field(
        ...,
        min_length=1
    )

    code: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="6-digit password reset code"
    )

class ResetPassword(BaseModel):

    reset_token: str = Field(
        ...,
        min_length=1
    )

    new_password: str = Field(
        ...,
        min_length=8
    )

class ForgetPassword(BaseModel):

    email: EmailStr

class Task(BaseModel):

    new_task: str = Field(
        ...,
        min_length=1,
        max_length=500
    )

class UpdateTask(BaseModel):

    task: str = Field(
        ...,
        min_length=1,
        max_length=500
    )

class TaskResponse(BaseModel):
    id: int
    task: str
    is_done: bool
    user_id: int

    model_config = ConfigDict(from_attributes=True)