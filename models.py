from sqlalchemy import (
    Integer,
    String,
    Column,
    ForeignKey,
    Boolean,
    DateTime
)

from database import Base

class User(Base):

    __tablename__ = "user"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        nullable=False,
        unique=True
    )

    email = Column(
        String,
        nullable=False,
        unique=True
    )

    hashed_password = Column(
        String,
        nullable=False
    )

    email_verified = Column(
        Boolean,
        nullable=False,
        default=False
    )

    verification_code = Column(
        String,
        nullable=True
    )

    verification_id = Column(
        String,
        unique=True,
        nullable=True
    )

    verification_code_expiry = Column(
        DateTime(timezone=True),
        nullable=True
    )

    verification_attempts = Column(
        Integer,
        nullable=False,
        default=0
    )

    reset_code = Column(
        String,
        nullable=True,
        default=None
    )

    reset_code_expiry = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    reset_id = Column(
        String,
        unique=True,
        nullable=True,
        default=None
    )

    reset_attempts = Column(
        Integer,
        nullable=False,
        default=0
    )

    token_session = Column(
        Integer,
        nullable=False,
        default=0
    )

class Todo(Base):

    __tablename__ = "task"

    id = Column(
        Integer,
        index=True,
        primary_key=True
    )

    task = Column(
        String,
        nullable=False
    )

    is_done = Column(
        Boolean,
        nullable=False,
        default=False
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "user.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )