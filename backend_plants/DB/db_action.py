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
action_data = [
    {
        'action_name': 'Добавление',
    },
        {
        'action_name': 'Изменение',
    },
        {
        'action_name': 'Удаление',
    }

]

# SQL-запрос для вставки нового растения
insert_query = """
    INSERT INTO "Action" (action_name)
    VALUES (%s)
"""

# Подготовка данных для вставки
insert_values = [(action['action_name'],) for action in action_data]

# Выполнение запроса с использованием executemany
cursor.executemany(insert_query, insert_values)

# Сохранение изменений
conn.commit()

# Закрытие соединения с базой данных
cursor.close()
conn.close()

print(f"Добавлены действия в базу данных.")
