import psycopg2

conn = psycopg2.connect(
    user="root",
    password="root",
    host="127.0.0.1",
    port="5432",
    database='plants_app_db'
)

cursor = conn.cursor()

type_rec_data = [
    {
        'type_rec_name': 'по растению',
    },
    {
        'type_rec_name': 'по коллекции',
    }
]

insert_query = """
    INSERT INTO "Type_Recommendation" (type_rec_name)
    VALUES (%s)
"""

insert_values = [(type_rec['type_rec_name'],) for type_rec in type_rec_data]

cursor.executemany(insert_query, insert_values)
conn.commit()


cursor.close()
conn.close()

print(f"Добавлены типы рекомендаций в базу данных.")
