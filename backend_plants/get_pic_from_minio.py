from minio import Minio
from minio.error import S3Error
import os
from django.conf import settings
from typing import List
from Backend_plants.serializers import *


def get_image_sizes(plant_list: List[Plant]):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_HOST,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )

    sizes = {}

    for plant in plant_list:
        img_obj_name = f"{plant.plant_name}.png"

        try:
            # Получаем объект изображения
            response = client.stat_object(settings.AWS_STORAGE_BUCKET_NAME, img_obj_name)
        except S3Error as e:
            print(f"Ошибка доступа к изображению {img_obj_name}: {e}")
        
        # Получаем размер файла
        size = response.size
        sizes[plant.plant_id] = {
            'plant_name': plant.plant_name,
            'image_size': size  # Размер в байтах
        }
        
        # Можно, например, сохранить файл локально
        # with client.get_object(settings.AWS_STORAGE_BUCKET_NAME, img_obj_name) as object_data:
        #     with open(os.path.join('images', img_obj_name), 'wb') as file_data:
        #         for d in object_data.stream(32 * 1024):  # Читаем по 32 Кб
        #             file_data.write(d)


        

        
        
        ## предполагаем, что у вас есть метод `get_feature_vector`, 
        ## который извлекает вектор признаков из изображения растения. 
        ## Вы должны реализовать этот метод, например, используя заранее 
        ## обученную модель (CNN или другую).


        # feature_vector_a = get_feature_vector(plant_list[0])  # замените на ваш метод получения векторов
        # feature_vector_b = get_feature_vector(plant_list[1])  # замените на ваш метод получения векторов
        
        # # Преобразуем векторы в numpy массивы
        # vector_a = np.array(feature_vector_a)
        # vector_b = np.array(feature_vector_b)

        # # Расчет косинусного расстояния
        # cosine_similarity = np.dot(vector_a, vector_b) / (np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
        # cosine_distance = 1 - cosine_similarity  # Превращаем в схему расстояния

        # print(f'Косинусное расстояние между и {plant_list[1].plant_name}: {cosine_distance}')
    return sizes


