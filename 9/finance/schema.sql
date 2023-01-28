

-- .SCHEMA --
-- CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 100000.00);

-- CREATE TABLE sqlite_sequence(name,seq);
-- CREATE UNIQUE INDEX username ON users (username);

-- CREATE TABLE assets (
--    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--    class TEXT NOT NULL, -- class: stock, etf, option, fx
--    symbol TEXT NOT NULL,
--    name TEXT NOT NULL
-- );

-- CREATE TABLE holdings (
--    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--    asset_id NUMERIC,
--    qty NUMERIC,
--    user_id NUMERIC,
--    FOREIGN KEY (asset_id) REFERENCES assets(id),
--    FOREIGN KEY (user_id) REFERENCES users(id)
-- );
-- CREATE TABLE trades (
--    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--    type TEXT, -- type: buy, sell
--    user_id INTEGER,
--    asset_id INTEGER,
--    qty REAL,
--    price REAL,
--    time TEXT, -- UTC
--    FOREIGN KEY (user_id) REFERENCES users(id),
--    FOREIGN KEY (asset_id) REFERENCES assets(id)
-- );
