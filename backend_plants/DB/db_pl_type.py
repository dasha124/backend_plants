import psycopg2

# Настройки подключения к базе данных
conn = psycopg2.connect(
    user="root",
    password="root",
    host="127.0.0.1",
    port="5432",
    database='plants_app_db'
)

cursor = conn.cursor()

# Примеры данных для вставки растений
plant_type_data = [
    {
        'type_name': 'Фикус',

    }
    # {
    #     'plant_name': 'Суккулент',
    #     'plant_class_id': 2,
    #     'plant_subclass_id': None,
    #     'image_url': 'http://example.com/image_of_plant2.jpg',
    #     'general_info': 'Суккуленты — это растения, которые хранят воду.',
    #     'properties': '{"light": "Full sun", "watering": "Low", "toxic": false}',
    #     'status': 'a'
    # },
    # {
    #     'plant_name': 'Кактус',
    #     'plant_class_id': 3,
    #     'plant_subclass_id': None,
    #     'image_url': 'http://example.com/image_of_plant3.jpg',
    #     'general_info': 'Кактусы — это колючие растения, которые также сохраняют воду.',
    #     'properties': '{"light": "Full sun", "watering": "Very low", "toxic": false}',
    #     'status': 'a'
    # }
]

# SQL-запрос для вставки нового растения
insert_query = """
    INSERT INTO "Plant_Type" (type_name)
    VALUES (%s)
"""

# Подготовка данных для вставки
insert_values = [(pl_type['type_name'],) for pl_type in plant_type_data]

# Выполнение запроса с использованием executemany
cursor.executemany(insert_query, insert_values)

# Сохранение изменений
conn.commit()

# Закрытие соединения с базой данных
cursor.close()
conn.close()

print(f"Добавлены виды растений в базу данных.")
