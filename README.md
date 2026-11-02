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

## Clerk authentication

The React frontend uses `@clerk/react` with sign-in and sign-up modals and a signed-in profile menu. The selected Clerk application is `app_3LWZuHJdpl2z945zfgHXiiOj6Bs`.

Development setup is connected to this application. Keys are stored locally in the ignored `frontend/.env.local` file. Email is the only enabled identifier: sign-up requires a password and email verification, and email codes are enabled for sign-in. Phone, username, social sign-in, passkeys, and Web3 sign-in are disabled.

To restore the development setup on another machine:

1. Run `npx -y clerk@latest auth login` in your host terminal using the account that owns the application.
2. From `frontend/`, run `npx -y clerk@latest link --app app_3LWZuHJdpl2z945zfgHXiiOj6Bs`, then `npx -y clerk@latest env pull` to fetch development keys. Do not overwrite working keys for a different application.
3. The frontend requires `VITE_CLERK_PUBLISHABLE_KEY` in its local environment. Never put a Clerk secret key in a `VITE_` variable. Environment and Clerk state files are ignored by Git.
4. Keep the email-only configuration in the Clerk Dashboard. These are application settings; frontend buttons alone do not enforce email-only authentication.
5. Run `npx -y clerk@latest doctor` and `npm run dev`. Open the local URL and sign up with your email; the profile menu appears after signing in.

The Django `/api/auth/login/` endpoint remains a development placeholder that returns a dummy token. It is not Clerk authentication and must not be used to authorize requests. Backend token verification and persistent user records have not been implemented.

The frontend returns users to the homepage after authentication or sign-out. Public job browsing remains available without signing in. To check the integration locally, open the Vite URL, select **Sign up**, verify your email, and confirm the profile menu appears in the top navigation. The profile menu provides account management and sign-out.
