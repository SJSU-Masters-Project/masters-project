# masters-project

SJSU Masters project — a two-sided job application portal for companies and students/job seekers.

## Structure

- `backend/` — Django API with a PyMongo connection layer.
- `frontend/` — React + Vite portal interface with company and candidate entry points.
- `experiments/` — isolated prototypes and research spikes.

## Local setup

1. Copy `.env.example` to `.env` and set `MONGODB_URI` / `MONGODB_DATABASE`.
2. Install backend dependencies with `pip install -r requirements.txt`.
3. Start the API: `cd backend && python manage.py runserver`.
4. In another terminal, run `cd frontend && npm install && npm run dev`.

The MongoDB integration uses PyMongo and currently exposes a health endpoint, login placeholder, and jobs listing endpoint. Authentication and document schemas can be expanded as the product requirements settle.
