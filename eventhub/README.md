# EventHub

Flask web portal for posting and browsing events.

## Structure
```
eventhub/
├── app.py              # all routes, error handlers, helpers (matches course example style)
├── config.py           # Config + TestConfig
├── models.py           # db instance, User, Event models
├── forms.py            # RegisterForm, LoginForm, EventForm, UpdateProfileForm
├── templates/          # flat templates (base, index, event, event_form, login, register, profile, about, 404, 500)
├── static/
│   ├── css/style.css
│   ├── profile_pics/
│   └── event_pics/
├── tests/               # pytest: routes, login, permissions
├── logs/app.log         # created automatically on first run
└── requirements.txt
```

`instance/eventhub.db` (SQLite) is created automatically on first run inside
an auto-generated `instance/` folder — this is standard Flask-SQLAlchemy
behavior for a relative sqlite URI, no need to create it manually.

## Features
- Registration / Login / Logout (hashed passwords via Flask-Bcrypt)
- Add / Edit / Delete events (owner-only, enforced via authorization checks -> 403 otherwise)
- Event list with category filter + sort (newest / oldest / event date) + pagination
- Event detail page with live weather for the event location (OpenWeatherMap)
- Profile page with editable name/email and profile picture
- 404 / 500 custom error pages
- File logging of key actions (logins, CRUD, API errors) -> logs/app.log
- Unit tests: routes, login, and permission checks (pytest) -> tests/

Default placeholder images (`static/profile_pics/default.jpg` and
`static/event_pics/default_event.jpg`) are included in the repo — new users
and events without an uploaded picture fall back to these automatically.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # then fill in SECRET_KEY and OPENWEATHER_API_KEY
```

Get a free OpenWeatherMap API key at https://openweathermap.org/api — the weather
chip on the event page silently disappears if the key is missing, so the app
still works without it.

## Run

```bash
python app.py
```

Visit http://127.0.0.1:5000

## Run tests

```bash
pytest
```

## Deployment
1. Push this repo to GitHub.
2. Deploy on Render / PythonAnywhere / Railway (any Python host).
3. Set the `SECRET_KEY`, `DATABASE_URL`, and `OPENWEATHER_API_KEY` environment
   variables on the host's dashboard — don't commit `.env`.
4. Point the start command at `app.py` (or use gunicorn: `gunicorn app:app`).
