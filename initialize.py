import sqlite3

#connecting to database
conn = sqlite3.connect('health_data.db')
cursor = conn.cursor()

#creating tables in database
cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        resting_hr INTEGER,
        max_hr INTEGER
    )
""")

#workout_hr_avg is a string with the average heart rate split across 10 sections
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cardio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warmup_min INTEGER,
        warmup_sec INTEGER,
        workout_min INTEGER,
        workout_sec INTEGER,
        cooldown_min INTEGER,
        cooldown_sec INTEGER,
        warmup_hr INTEGER,
        workout_hr INTEGER,
        workout_hr_avg TEXT,
        cooldown_hr INTEGER,
        workout_spo2 INTEGER,
        quality INTEGER
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_layout (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        rep INTEGER
    )
""")

#the strength part is comma seperated between each different exercise
cursor.execute("""
    CREATE TABLE IF NOT EXISTS strengthtp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_ids TEXT,
        exercise_name TEXT,
        expect_rep TEXT,
        rep TEXT,
        load TEXT,
        exercise_min TEXT,
        exercise_sec TEXT,
        exercise_hr TEXT,
        exercise_spo2 TEXT,
        quality TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        cardio_id INTEGER,
        strengthtp_id INTEGER,
        date TEXT
    )
""")

conn.commit()
conn.close()
