# Chess Platform Backend

A focused multiplayer chess API built to learn backend software engineering. It
supports account authentication, private two-player games, legal chess moves,
and persistent game state. The project is intentionally backend-only and small
enough to inspect as a Python code sample.

## Technology

- Python, FastAPI, Pydantic
- SQLAlchemy with PostgreSQL
- `python-chess` for chess rules
- passlib/bcrypt for password hashing
- signed JWT bearer tokens with python-jose
- pytest, FastAPI TestClient, and isolated SQLite tests

## Implemented features

- Registration, login, JWT validation, and `GET /auth/me`
- Private game creation by opponent username
- Participant-only game retrieval and per-user game lists
- Server-authoritative turn and legal-move validation
- UCI move input, SAN move output, FEN board state, and valid PGN history
- Checkmate and draw detection through `python-chess`
- Focused authentication, authorization, game, and move tests

Clocks, resignations, draw offers, ratings, matchmaking, WebSockets, and a
frontend are not implemented.

## Architecture

```text
.
├── backend/
│   ├── app/
│   │   ├── core/          # settings, database sessions, password/JWT helpers
│   │   ├── models/        # SQLAlchemy User and Game tables
│   │   ├── routes/        # FastAPI authentication and game endpoints
│   │   ├── schemas/       # validated request and response contracts
│   │   └── services/      # chess rules, PGN, FEN, and outcome logic
│   ├── migrations/        # PostgreSQL migration for an existing database
│   ├── tests/             # isolated API and service tests
│   ├── create_tables.py
│   └── main.py
├── .env.example
└── requirements.txt
```

### Request and trust boundaries

Registration hashes passwords before persistence. Login verifies the hash and
returns a signed JWT whose `sub` identifies the user. Protected routes decode
that token, load the active user, and never accept a client-supplied user ID.

Game routes authorize access by comparing the authenticated user ID with the
stored white and black player IDs. An unrelated authenticated user therefore
cannot read or modify a private game.

A move follows this flow:

```text
JWT authentication → game lookup → participant authorization → active check
→ row lock → board from FEN → turn ownership → UCI parse → legal-move check
→ SAN calculation → apply move → FEN and PGN update → outcome → commit
```

The backend is the source of truth because a client can tamper with any value
it sends. The client supplies only a UCI move such as `e2e4`; identity, color,
turn, board position, and ownership come from the JWT and database.

FEN stores the exact current position needed to validate the next move without
replaying the entire game. PGN separately stores a standards-based, portable,
human-readable replay history. Before appending a move, the service checks that
the PGN's final position matches the stored FEN.

## Local setup

Python 3.10 or later and PostgreSQL are required for normal development.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Create a PostgreSQL database, for example:

```sql
CREATE DATABASE chess_db;
```

Edit `.env` with your local connection string and a long random JWT secret:

```dotenv
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/chess_db
SECRET_KEY=your_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Never commit `.env`. For a new empty database, create the tables from the
backend directory:

```powershell
cd backend
python create_tables.py
```

`create_all()` creates missing tables but does not alter existing ones. If the
`games` table already exists, apply
`backend/migrations/001_add_game_board_state.sql` with PostgreSQL tooling:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_add_game_board_state.sql
```

## Run and explore the API

From `backend`:

```bash
uvicorn main:app --reload
```

Open Swagger UI at <http://127.0.0.1:8000/docs>. Use the returned login token
with Swagger's **Authorize** button or an `Authorization: Bearer <token>`
header.

Example request bodies:

Register:

```json
{
  "username": "white_player",
  "email": "white@example.com",
  "password": "strongpass123"
}
```

Login:

```json
{
  "username": "white_player",
  "password": "strongpass123"
}
```

Create a game:

```json
{
  "opponent_username": "black_player",
  "time_control": "rapid",
  "play_as": "white"
}
```

Submit `POST /games/{game_id}/move`:

```json
{
  "move": "e2e4"
}
```

Promotions use standard UCI notation such as `e7e8q`.

## Tests

From `backend`:

```bash
pytest -q
```

Tests set test-only environment values before importing the application,
override the database dependency, and use a shared in-memory SQLite engine.
Tables are recreated for each test, so the developer's PostgreSQL database is
never touched.

SQLite does not prove PostgreSQL row-lock behavior. In production PostgreSQL,
`SELECT ... FOR UPDATE` serializes concurrent move updates for one game; SQLite
ignores that clause.

## Current limitations and focused future work

- Draw claims supported by `python-chess` are treated as automatic completion
  because the API has no separate claim-draw action.
- No Alembic migration framework; one explicit SQL migration covers this
  focused schema change.
- No clocks, timeouts, resignations, draw offers, spectators, or live updates.
- PGN headers contain defaults rather than player profile metadata.
- Integration testing against PostgreSQL would strengthen concurrency coverage.

Reasonable next steps are an explicit resign/draw workflow, PostgreSQL
integration tests, richer PGN headers, and live game updates after the core
API remains stable.
