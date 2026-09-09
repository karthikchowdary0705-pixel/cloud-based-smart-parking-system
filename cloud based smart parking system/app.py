from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "parking.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            vehicle_number TEXT,
            owner_name TEXT,
            entry_time TEXT
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    count = cursor.fetchone()[0]

    if count == 0:
        for i in range(1, 21):
            cursor.execute("""
                INSERT INTO parking_slots (slot_number, status)
                VALUES (?, ?)
            """, (f"P{i}", "Available"))

    conn.commit()
    conn.close()


def get_slots():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM parking_slots
        ORDER BY id
    """)

    slots = cursor.fetchall()
    conn.close()

    return slots


def get_counts():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM parking_slots
        WHERE status = 'Available'
    """)
    available = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM parking_slots
        WHERE status = 'Occupied'
    """)
    occupied = cursor.fetchone()[0]

    conn.close()

    return available, occupied


@app.route("/")
def index():
    slots = get_slots()
    available, occupied = get_counts()
    total = available + occupied

    return render_template(
        "index.html",
        slots=slots,
        available=available,
        occupied=occupied,
        total=total,
        message=None
    )


@app.route("/reserve", methods=["POST"])
def reserve():
    slot_number = request.form["slot_number"]
    vehicle_number = request.form["vehicle_number"]
    owner_name = request.form["owner_name"]

    entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE parking_slots
        SET status = 'Occupied',
            vehicle_number = ?,
            owner_name = ?,
            entry_time = ?
        WHERE slot_number = ?
        AND status = 'Available'
    """, (
        vehicle_number,
        owner_name,
        entry_time,
        slot_number
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/release/<int:slot_id>")
def release(slot_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT entry_time
        FROM parking_slots
        WHERE id = ?
    """, (slot_id,))

    result = cursor.fetchone()

    fee = 0

    if result and result[0]:
        entry_time = datetime.strptime(
            result[0],
            "%Y-%m-%d %H:%M:%S"
        )

        exit_time = datetime.now()
        duration = exit_time - entry_time

        hours = duration.total_seconds() / 3600
        hours = max(1, hours)

        fee = round(hours * 20, 2)

    cursor.execute("""
        UPDATE parking_slots
        SET status = 'Available',
            vehicle_number = NULL,
            owner_name = NULL,
            entry_time = NULL
        WHERE id = ?
    """, (slot_id,))

    conn.commit()
    conn.close()

    slots = get_slots()
    available, occupied = get_counts()

    return render_template(
        "index.html",
        slots=slots,
        available=available,
        occupied=occupied,
        total=available + occupied,
        message=f"Parking released successfully! Parking Fee: ₹{fee}"
    )


if __name__ == "__main__":
    init_db()

    print("----------------------------------")
    print(" Smart Parking System Started")
    print("----------------------------------")
    print("Open: http://127.0.0.1:5000")

    app.run(debug=True)