from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from database import Base, get_db, engine
from typing import Annotated

from models import User, Todo

from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError
)

import auth as auth

from auth import get_current_user

from schemas import (
    ChangePassword,
    Task,
    UpdateTask,
    TaskResponse
)

from dotenv import load_dotenv
import os

load_dotenv()

Base.metadata.create_all(engine)

frontend_url = os.getenv("FRONTEND_URL")

if not frontend_url:
    raise RuntimeError(
        "FRONTEND_URL is not configured"
    )

app = FastAPI()

app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

db_dependency = Annotated[
    Session,
    Depends(get_db)
]

user_dependency = Annotated[
    User,
    Depends(get_current_user)
]

@app.get("/")
async def profile(
    user: user_dependency
):
    return {
        "username": user.username
    }

@app.patch("/password-change")
async def change_password(
    password: ChangePassword,
    user: user_dependency,
    db: db_dependency
):
    try:
        auth.ph.verify(
            user.hashed_password,
            password.old_password
        )

    except (
        VerifyMismatchError,
        VerificationError
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )

    if password.old_password == password.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different"
        )

    user.hashed_password = auth.ph.hash(
        password.new_password
    )

    # Invalidate all tokens issued before
    # the password change.
    user.token_session += 1

    db.commit()

    return {
        "message": "Password changed successfully"
    }

@app.post("/logout-all")
async def logout_all(
    user: user_dependency,
    db: db_dependency
):
    user.token_session += 1

    db.commit()

    return {
        "message": "Logged out from all devices"
    }

@app.post(
    "/task",
    status_code=status.HTTP_201_CREATED
)
async def create_task(
    user: user_dependency,
    task: Task,
    db: db_dependency
):
    new_task = Todo(
        task=task.new_task,
        user_id=user.id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "message": "New task has been created"
    }

# Tell FastAPI that this returns a list of TaskResponse schemas
@app.get("/get-task", response_model=list[TaskResponse])
async def get_task(
    user: user_dependency,
    db: db_dependency
):
    tasks = (
        db.query(Todo)
        .filter(Todo.user_id == user.id)
        .all()
    )
    # FastAPI will automatically use response_model to safely convert these to JSON
    return tasks 


@app.patch("/task/{task_id}/done")
async def done(
    task_id: int,
    user: user_dependency,
    db: db_dependency
):
    task = (
        db.query(Todo)
        .filter(
            Todo.id == task_id,
            Todo.user_id == user.id
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    task.is_done = True

    db.commit()
    db.refresh(task)

    return {
        "message": "Task marked as done",
        # Manually convert the SQLAlchemy object to a dictionary using the new schema
        "task": TaskResponse.model_validate(task).model_dump()
    }

@app.patch("/task/{task_id}")
async def update(
    task_id: int,
    update_task: UpdateTask,
    db: db_dependency,
    user: user_dependency
):
    task = (
        db.query(Todo)
        .filter(
            Todo.id == task_id,
            Todo.user_id == user.id
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    task.task = update_task.task

    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated successfully"
    }
    
@app.delete("/task/{task_id}")
async def delete(
    task_id: int,
    db: db_dependency,
    user: user_dependency
):
    task = (
        db.query(Todo)
        .filter(
            Todo.id == task_id,
            Todo.user_id == user.id
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    return {
        "message": "Task deleted successfully"
    }
    
@app.delete("/account")
async def delete_account(
    user: user_dependency,
    db: db_dependency
):
    db.delete(user)
    db.commit()

    return {
        "message": "Account deleted successfully"
    }