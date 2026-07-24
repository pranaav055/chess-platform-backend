-- Apply this migration once to an existing PostgreSQL database.
-- New installations can use `python backend/create_tables.py` instead.
BEGIN;

ALTER TABLE games
    ADD COLUMN current_fen TEXT;

UPDATE games
SET current_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
WHERE current_fen IS NULL;

-- The previous application created all games as "waiting" and had no move API.
UPDATE games SET status = 'active' WHERE status = 'waiting';

ALTER TABLE games
    ALTER COLUMN current_fen SET NOT NULL,
    ALTER COLUMN current_fen SET DEFAULT
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
    ALTER COLUMN status SET DEFAULT 'active';

UPDATE games SET pgn = '' WHERE pgn IS NULL;
ALTER TABLE games
    ALTER COLUMN pgn SET NOT NULL,
    ALTER COLUMN pgn SET DEFAULT '';

COMMIT;
