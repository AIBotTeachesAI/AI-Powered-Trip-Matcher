import sqlite3

# Assumes a SQLite DB file exists with a 'demand' table:
# CREATE TABLE demand (origin TEXT, destination TEXT, count INTEGER);

"""
sqlite3 repositioning.db

CREATE TABLE demand (
    origin TEXT,
    destination TEXT,
    count INTEGER
);

INSERT INTO demand (origin, destination, count) VALUES ('San Francisco', 'Las Vegas', 12);
INSERT INTO demand (origin, destination, count) VALUES ('San Francisco', 'Los Angeles', 9);
INSERT INTO demand (origin, destination, count) VALUES ('San Francisco', 'New York', 4);
INSERT INTO demand (origin, destination, count) VALUES ('San Francisco', 'Chicago', 3);
INSERT INTO demand (origin, destination, count) VALUES ('Las Vegas', 'San Francisco', 8);
INSERT INTO demand (origin, destination, count) VALUES ('Las Vegas', 'Los Angeles', 10);
INSERT INTO demand (origin, destination, count) VALUES ('Los Angeles', 'San Francisco', 11);
INSERT INTO demand (origin, destination, count) VALUES ('Los Angeles', 'Chicago', 5);
INSERT INTO demand (origin, destination, count) VALUES ('New York', 'Chicago', 7);
INSERT INTO demand (origin, destination, count) VALUES ('New York', 'San Francisco', 6);

.quit

"""


DB_PATH = "repositioning.db"

def suggest_repositioning(trip):
    current_location = trip.get("origin")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query top 3 destinations from current location based on past demand
    cursor.execute("""
        SELECT destination, count FROM demand
        WHERE origin = ?
        ORDER BY count DESC LIMIT 3
    """, (current_location,))
    rows = cursor.fetchall()
    conn.close()

    suggestions = [{"destination": dest, "demand": cnt} for dest, cnt in rows]
    return {"reposition_suggestions": suggestions}

