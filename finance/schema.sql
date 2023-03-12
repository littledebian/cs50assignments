CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    cash NUMERIC NOT NULL DEFAULT 10000.00
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE UNIQUE INDEX username ON users (username);
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC
);
CREATE TABLE holdings (
    asset_id INTEGER,
    user_id INTEGER,
    qty NUMERIC,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE (asset_id,user_id)
);
CREATE TABLE trades (
    type TEXT NOT NULL,
    asset_id INTEGER,
    user_id INTEGER,
    shares NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);