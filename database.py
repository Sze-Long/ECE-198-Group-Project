import sqlite3

DATABASE = "health_data.db"

#gets all patients
def get_patients():

    conn = sqlite3.connect("health_data.db")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM patient
            ORDER BY name
        """)

        return cursor.fetchall()

    finally:
        conn.close()

#gets a specific patient data
def get_patient(patient_id):

    conn = sqlite3.connect("health_data.db")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM patient
            WHERE id = ?
        """, (patient_id,))

        return cursor.fetchone()

    finally:
        conn.close()

#gets all the exercises
def get_exercises():

    conn = sqlite3.connect("health_data.db")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM exercise_layout
            ORDER BY name
        """)

        return cursor.fetchall()

    finally:
        conn.close()

#gets the numebr pf reps for that exercise
def get_exercise_rep(exercise_id):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT rep
            FROM exercise_layout
            WHERE id = ?
        """, (exercise_id,))

        result = cursor.fetchone()

        if result is None:
            return None

        return result[0]

    finally:
        conn.close()

#get all workouts for a patient
def get_workouts(patient_id):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM workout
            WHERE patient_id = ?
            ORDER BY date DESC, id DESC
        """, (patient_id,))

        return cursor.fetchall()

    finally:
        conn.close()

#get one specific workout
def get_workout(workout_id):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM workout
            WHERE id = ?
        """, (workout_id,))

        return cursor.fetchone()

    finally:
        conn.close()


#saves a workout to the database
#Eg: 2,1,1,20cardionumbers,exercise#,9exercisenumbers(comma seperated)
def save_workout(data):
    
    values = data.split(",")
    patient_id = int(values[0])
    cardio_val = int(values[1])
    exercise_val = int(values[2])

    read_values = 3

    cardio_id = 0
    strengthtp_id = 0

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:

        if cardio_val == 1:

            cardio_values = values[read_values:read_values + 21]
            read_values += 21

            #10 average heart rates
            hr_avg = ",".join(cardio_values[8:18])

            #putting cardio data into tuple
            cardio_data = (
                cardio_values[:8]
                + [hr_avg]
                + cardio_values[18:21]
            )

            #putting data into cardio table in database
            cursor.execute("""
                INSERT INTO cardio (
                    warmup_min,
                    warmup_sec,
                    workout_min,
                    workout_sec,
                    cooldown_min,
                    cooldown_sec,
                    warmup_hr,
                    workout_hr,
                    workout_hr_avg,
                    cooldown_hr,
                    workout_spo2,
                    quality
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cardio_data)

            cardio_id = cursor.lastrowid

        if exercise_val == 1:
            
            exercise_count = int(values[read_values])
            read_values += 1
            
            #put all data into exercise array
            exercise_data = []

            #repeat for each parameter
            for i in range(10):
                temp = ",".join(values[read_values:read_values+exercise_count])
                exercise_data.append(temp)
                read_values += exercise_count

            strength_data = tuple(exercise_data)

            cursor.execute("""
                INSERT INTO strengthtp (
                    exercise_ids,
                    exercise_name,
                    expect_rep,
                    rep,
                    load,
                    exercise_min,
                    exercise_sec,
                    exercise_hr,
                    exercise_spo2,
                    quality
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, strength_data)

            strengthtp_id = cursor.lastrowid

        # 3. Create workout
        cursor.execute("""
            INSERT INTO workout (
                patient_id,
                cardio_id,
                strengthtp_id,
                date
            )
            VALUES (?, ?, ?, DATE('now', 'localtime'))
        """, (patient_id, cardio_id, strengthtp_id))

        workout_id = cursor.lastrowid

        conn.commit()

        return workout_id

    except sqlite3.Error as e:
        conn.rollback()
        print("workout creation error", e)
    finally:
        conn.close()


#makes a new patient
def create_patient(name, age, resting_hr, max_hr):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO patient (name, age, resting_hr, max_hr)
            VALUES (?, ?, ?, ?)
        """, (name, age, resting_hr, max_hr))

        patient_id = cursor.lastrowid
        conn.commit()

        return patient_id

    except sqlite3.Error as e:
        conn.rollback()
        print("create patient error", e)
        return None

    finally:
        conn.close()


#edit current patient
def edit_patient(patient_id, name, age, resting_hr, max_hr):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        #get patient data
        cursor.execute("""
            SELECT name, age, resting_hr, max_hr
            FROM patient
            WHERE id = ?
        """, (patient_id,))

        patient = cursor.fetchone()

        if patient is None:
            return False

        cursor.execute("""
            UPDATE patient
            SET name = ?,
                age = ?,
                resting_hr = ?,
                max_hr = ?
            WHERE id = ?
        """, (
            name,
            age,
            resting_hr,
            max_hr,
            patient_id
        ))

        conn.commit()

        return True

    except sqlite3.Error as e:
        conn.rollback()
        print("edit patient error", e)
        return False

    finally:
        conn.close()


#creating new exercises
def create_exercise(name, rep):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO exercise_layout (name, rep)
            VALUES (?, ?)
        """, (name, rep))

        exercise_id = cursor.lastrowid

        conn.commit()

        return exercise_id

    except sqlite3.Error as e:
        conn.rollback()
        print("create exercise error", e)
        return None

    finally:
        conn.close()

#editing exercises
def edit_exercise(exercise_id, name, rep):

    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE exercise_layout
            SET name = ?,
                rep = ?
            WHERE id = ?
        """, (name, rep, exercise_id))

        conn.commit()

        return cursor.rowcount > 0

    except sqlite3.Error as e:
        conn.rollback()
        print("edit exercise error:", e)
        return False

    finally:
        conn.close()
