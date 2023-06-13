BEGIN;

CREATE TABLE IF NOT EXISTS posts (
	short_id TEXT PRIMARY KEY, -- i don't think there's a "formal" guarantee of short_id stability, but it's UNIQUE in the current lobste.rs schema, so whatever
	created_ts INTEGER NOT NULL,
	title TEXT NOT NULL,
	url TEXT,
	tags TEXT -- space separated, sorted alphabetically

	-- It might be good to store the poster too?  I don't really see the point
	-- of that, though.  Also, if I were to release the data publicly, not
	-- having poster data would probably be for the better.
);

-- In theory this is unnecessary right now, but it could come in handy if the
-- trigger approach turns out to be flawed.
CREATE TABLE IF NOT EXISTS scores (
	short_id TEXT NOT NULL,
	fetch_ts INTEGER NOT NULL,
	score NOT NULL,

	FOREIGN KEY (short_id)
		REFERENCES posts (short_id)
			ON DELETE CASCADE
			ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS score_after (
	short_id TEXT NOT NULL,
	after INTEGER NOT NULL,
	score NOT NULL,

	UNIQUE (short_id, after),

	FOREIGN KEY (short_id)
		REFERENCES posts (short_id)
			ON DELETE CASCADE
			ON UPDATE NO ACTION
);

-- Is this stupid?
CREATE TRIGGER IF NOT EXISTS score_after_24h
AFTER INSERT ON scores
FOR EACH ROW
WHEN (
	SELECT created_ts
	FROM posts
	WHERE short_id = new.short_id
) + 60 * 60 * 24 <= new.fetch_ts
BEGIN
	INSERT OR IGNORE -- if it was already inserted, fetch_ts will always be smaller
	                 -- unless the server time travels
	INTO score_after (short_id, after, score)
	VALUES (new.short_id, 60 * 60 * 24, new.score);
END;

CREATE INDEX IF NOT EXISTS scores_id_idx ON scores (short_id);

PRAGMA foreign_keys = ON;

COMMIT;
