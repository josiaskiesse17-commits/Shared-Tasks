# Shared Household Chores Manager

Django MVP for managing chores in one shared household.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser. The first signup creates an Admin and household. Admins can add Members or share the generated invite code.

## Development commands

Run the full app test suite:

```powershell
.\.venv\Scripts\python.exe manage.py test chores
```

Check Django configuration:

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Create migrations after model changes:

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
```

The MVP intentionally excludes push/email notifications, chat, payments, gamification, multiple households per user, complex analytics, uploads, and third-party authentication.
