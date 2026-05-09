# Handwriting Recognition System with Custom Dataset Support

## Overview

A handwriting recognition system that supports custom datasets and now includes a built-in Admin UI (FastAPI + Jinja2 templates).

## Features

- Custom dataset creation and listing
- Student creation and listing by dataset
- Handwriting sample upload per student
- Handwriting prediction with configurable threshold
- Admin/Operator web UI at `/admin`
- Existing REST API endpoints remain available

## Project Structure

```
app/
├── main.py
├── models.py
├── schemas.py
├── database.py
├── crud.py
├── ml.py
├── ml_engine.py
├── static/
│   └── admin.css
├── templates/
│   └── admin.html
└── routers/
    ├── datasets.py
    ├── samples.py
    └── students.py
uploads/
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

- API root: `http://127.0.0.1:8000/`
- Admin UI: `http://127.0.0.1:8000/admin`
- API docs: `http://127.0.0.1:8000/docs`

## Existing API Endpoints (still available)

- `POST /datasets/`
- `GET /datasets/`
- `POST /students/`
- `GET /students/{dataset_id}`
- `POST /samples/{student_id}`
- `POST /predict/`
- `GET /samples/`
