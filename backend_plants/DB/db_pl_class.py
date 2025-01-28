import psycopg2

conn = psycopg2.connect(
    user="root",
    password="root",
    host="127.0.0.1",
    port="5432",
    database='plants_app_db'
)

cursor = conn.cursor()

plant_class_data = [
    {
        'class_name': 'Домашнее',
    }
]

insert_query = """
    INSERT INTO "Plant_Class" (class_name)
    VALUES (%s)
"""

insert_values = [(pl_class['class_name'],) for pl_class in plant_class_data]

cursor.executemany(insert_query, insert_values)
conn.commit()


cursor.close()
conn.close()

print(f"Добавлены классы растения в базу данных.")
