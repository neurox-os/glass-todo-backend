# Todo Application — Backend

The backend of the Todo Application is a RESTful API built with **FastAPI and PostgreSQL**. It handles authentication, authorization, user management, Todo operations, email verification, password management, and database communication.

The backend is designed as the central application layer between the frontend and the PostgreSQL database.

---

## Overview

```text
┌──────────────────────────┐
│        Frontend          │
│   HTML + CSS + JS        │
└────────────┬─────────────┘
             │
             │ REST API
             ▼
┌──────────────────────────┐
│     FastAPI Backend      │
│                          │
│ Authentication           │
│ Authorization            │
│ Todo Management          │
│ User Management          │
│ Email Verification       │
└────────────┬─────────────┘
             │
             │ SQLAlchemy
             ▼
┌──────────────────────────┐
│       PostgreSQL         │
└──────────────────────────┘
```

---

# Tech Stack

| Technology     | Purpose                               |
| -------------- | ------------------------------------- |
| Python         | Backend programming language          |
| FastAPI        | REST API framework                    |
| PostgreSQL     | Relational database                   |
| SQLAlchemy 2.0 | ORM and database interaction          |
| Pydantic       | Data validation                       |
| PyJWT          | JWT authentication                    |
| Argon2id       | Password hashing                      |
| FastAPI-Mail   | Email verification and password reset |
| Uvicorn        | ASGI server                           |
| python-dotenv  | Environment configuration             |

---

# Features

## Authentication

The backend provides a complete authentication system including:

* User registration
* Email verification
* Login
* JWT access tokens
* Refresh tokens
* HttpOnly refresh-token cookies
* Token session invalidation
* Logout-all functionality

---

## Authorization

The application separates authentication from authorization.

**Authentication** determines who the user is.

**Authorization** determines which resources the authenticated user is allowed to access.

Each Todo belongs to a specific user, and protected Todo endpoints verify ownership before performing operations.

```text
Authenticated User
        │
        ▼
   User ID
        │
        ▼
   Todo Query
        │
        ▼
Todo belongs to user?
        │
    ┌───┴───┐
   Yes      No
    │        │
    ▼        ▼
 Allow     Reject
```

This prevents users from accessing or modifying another user's Todo items.

---

# Password Security

User passwords are never stored in plaintext.

The backend uses **Argon2id** for password hashing.

```text
User Password
      │
      ▼
   Argon2id
      │
      ▼
Password Hash
      │
      ▼
 PostgreSQL
```

During login, the supplied password is verified against the stored Argon2id hash.

The application also supports Argon2 rehashing when the stored hash no longer meets the configured parameters.

---

# Email Verification

New accounts require email verification.

The verification process uses a randomly generated six-digit code.

```text
Signup
  │
  ▼
Generate 6-digit code
  │
  ▼
Hash verification code
  │
  ▼
Store hash in database
  │
  ▼
Send code through email
  │
  ▼
User submits code
  │
  ▼
Verify code
  │
  ▼
Account verified
```

Verification codes:

* Contain six digits
* Expire after a limited period
* Are stored as hashes
* Have a limited number of verification attempts

---

# JWT Authentication

The backend uses JWTs for authentication.

Two types of tokens are used:

### Access Token

* Short-lived
* Used to access protected API endpoints
* Sent with authenticated requests

### Refresh Token

* Longer-lived
* Stored in an HttpOnly cookie
* Used to obtain a new access token

```text
Login
 │
 ├──────────────► Access Token
 │                    │
 │                    ▼
 │              Protected APIs
 │
 └──────────────► Refresh Token
                      │
                      ▼
                HttpOnly Cookie
```

JWTs contain information such as:

* User identity
* Token type
* Token session version
* Expiration time

---

# Session Invalidation

The backend maintains a `token_session` value for each user.

When a security-sensitive action occurs, such as:

* Password change
* Password reset
* Logout-all

the session version is incremented.

Existing tokens containing the previous session version then become invalid.

```text
Old Token
token_session = 3
       │
       ▼
Password Changed
       │
       ▼
Database session = 4
       │
       ▼
Old token rejected
```

This provides a simple mechanism for invalidating previously issued authentication tokens.

---

# Password Reset

The backend provides a password-reset flow using email verification.

```text
Forgot Password
       │
       ▼
Generate reset code
       │
       ▼
Hash code
       │
       ▼
Send code by email
       │
       ▼
Verify reset code
       │
       ▼
Generate short-lived reset token
       │
       ▼
Set new password
       │
       ▼
Invalidate existing sessions
```

Reset codes are time-limited and have a maximum number of verification attempts.

---

# Todo Management

Authenticated users can:

* Create Todos
* Retrieve their Todos
* Update Todos
* Mark Todos as completed
* Delete Todos
* Delete their account

Every Todo is associated with a user through `user_id`.

```text
User
 │
 ├── Todo 1
 ├── Todo 2
 └── Todo 3
```

Todo queries include ownership checks to ensure users can only manage their own tasks.

---

# Database

The application uses **PostgreSQL** as its database and **SQLAlchemy 2.0** as its ORM.

The primary models are:

```text
User
 │
 │ 1
 │
 │ *
 ▼
Todo
```

The Todo table contains a foreign key referencing the User table.

The foreign key uses:

```text
ON DELETE CASCADE
```

so deleting a user also removes the user's associated Todo records.

---

# Database Initialization

The application currently uses SQLAlchemy's metadata creation mechanism to create the database tables.

```python
Base.metadata.create_all(engine)
```

This approach is suitable for this learning project and local development.

For a larger production application with frequent schema changes, a dedicated database migration system would be preferable.

---

# Backend Structure

```text
backend/
│
├── main.py
├── auth.py
├── database.py
├── models.py
├── schemas.py
├── email_verify.py
├── requirements.txt
├── .env
└── .gitignore
```

---

## `main.py`

The main FastAPI application.

Responsible for:

* FastAPI application setup
* CORS configuration
* Todo endpoints
* User endpoints
* Password management
* Account management
* Database interaction

---

## `auth.py`

Contains the authentication system.

Responsible for:

* User registration
* Email verification
* Login
* JWT creation
* Access-token validation
* Refresh-token handling
* Password verification
* Password reset
* Authentication dependencies
* Session invalidation

---

## `database.py`

Handles database configuration and SQLAlchemy sessions.

Responsibilities include:

* Loading the database URL
* Creating the SQLAlchemy engine
* Creating database sessions
* Defining the SQLAlchemy declarative base
* Providing database dependencies to FastAPI endpoints

---

## `models.py`

Contains the SQLAlchemy database models.

Primary models:

```text
User
Todo
```

The models define the database tables, columns, constraints, and relationships between application entities.

---

## `schemas.py`

Contains Pydantic schemas used for request validation.

Schemas are used for operations such as:

* User registration
* Email verification
* Password changes
* Password resets
* Todo creation
* Todo updates
* Token responses

---

## `email_verify.py`

Handles email-related functionality.

It is responsible for sending:

* Email verification codes
* Password reset codes

The application uses SMTP through FastAPI-Mail.

---

# API Endpoints

## Authentication

| Method | Endpoint                  | Description                 |
| ------ | ------------------------- | --------------------------- |
| POST   | `/auth/signup`            | Register a new user         |
| POST   | `/auth/verify-email`      | Verify email address        |
| POST   | `/auth/user-login`        | Authenticate user           |
| POST   | `/auth/refresh`           | Generate a new access token |
| POST   | `/auth/forgot-password`   | Start password reset        |
| POST   | `/auth/verify-reset-code` | Verify reset code           |
| POST   | `/auth/reset-password`    | Set a new password          |

---

## User

| Method | Endpoint           | Description                |
| ------ | ------------------ | -------------------------- |
| GET    | `/`                | Get current user           |
| POST   | `/password-change` | Change password            |
| POST   | `/logout-all`      | Invalidate active sessions |
| DELETE | `/account`         | Delete account             |

---

## Todo

| Method | Endpoint               | Description           |
| ------ | ---------------------- | --------------------- |
| POST   | `/task`                | Create a Todo         |
| GET    | `/get-task`            | Retrieve user's Todos |
| PATCH  | `/task/{task_id}`      | Update a Todo         |
| PATCH  | `/task/{task_id}/done` | Toggle completion     |
| DELETE | `/task/{task_id}`      | Delete a Todo         |

---

# Environment Variables

The backend uses environment variables to keep configuration and sensitive information outside the source code.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/todo_app

SECRET_KEY=your-secret-key
ALGORITHM=HS256

MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME=Todo Application

FRONTEND_URL=http://localhost:5500

COOKIE_SECURE=false
```

### Important

The `.env` file should **never be committed to Git**.

Add it to `.gitignore`:

```gitignore
.env
.venv/
venv/
__pycache__/
*.py[cod]
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repository.git
cd backend
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure PostgreSQL

Create a PostgreSQL database and configure its connection string in `.env`.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/todo_app
```

---

## 5. Configure Email

For Gmail SMTP, use a **Google App Password** rather than your normal Gmail account password.

Configure:

```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME=Todo Application
```

---

# Running the Backend

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative API documentation:

```text
http://127.0.0.1:8000/redoc
```

---

# CORS

The backend uses FastAPI's CORS middleware to allow requests from the configured frontend origin.

The frontend URL is configured through:

```env
FRONTEND_URL=http://localhost:5500
```

For deployment, this should be changed to the actual frontend domain.

---

# Security

The backend implements several fundamental security practices:

* Argon2id password hashing
* Hashed verification codes
* Hashed password-reset codes
* Short-lived access tokens
* HttpOnly refresh-token cookies
* Token session invalidation
* User-specific authorization
* Pydantic input validation
* CORS configuration
* Environment-based secrets
* OTP attempt limits
* Expiring verification and reset codes
* PostgreSQL foreign-key constraints

The project is primarily a **learning and portfolio application** and should not be considered an enterprise-grade authentication system.

---

# Development Philosophy

This backend was built to gain practical experience with real-world backend concepts rather than simply implementing a basic Todo CRUD API.

The project covers:

* REST API development
* Authentication
* Authorization
* Password security
* JWT
* Access and refresh tokens
* Email verification
* Password reset
* PostgreSQL
* SQLAlchemy
* FastAPI dependency injection
* Pydantic validation
* CORS
* Environment configuration
* Frontend/backend integration

---

# Future Improvements

Possible improvements for a larger application include:

* Automated testing
* OAuth/OIDC authentication
* More advanced rate limiting
* Refresh-token rotation
* Dedicated session management
* CI/CD
* Monitoring and logging
* Improved observability
* Production database migration management

These features are outside the current scope of the project.

---

## Author

**Adiptya Kundu**

B.Tech CSE (AI)
University of Engineering and Management, Kolkata
