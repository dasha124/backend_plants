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
plants_data = [
    {
        'plant_name': 'Мох',
        'plant_class_id': 1,
        'plant_subclass_id': None,
        'image_url': 'http://example.com/image_of_plant1.jpg',
        'general_info': 'Мох — это небольшое высшее растение.',
        'properties': '{"light": "Partial shade", "watering": "Moderate", "toxic": false}',
        'status': 'a'
    },
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
    INSERT INTO "Plant" (plant_name, plant_class_id, plant_subclass_id, image_url, general_info, properties, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

# Подготовка данных для вставки
insert_values = [(plant['plant_name'], 
                  plant['plant_class_id'], 
                  plant['plant_subclass_id'], 
                  plant['image_url'], 
                  plant['general_info'], 
                  plant['properties'], 
                  plant['status']) for plant in plants_data]

# Выполнение запроса с использованием executemany
cursor.executemany(insert_query, insert_values)

# Сохранение изменений
conn.commit()

# Закрытие соединения с базой данных
cursor.close()
conn.close()

print(f"Добавлены растения в базу данных.")
