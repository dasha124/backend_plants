from minio import Minio
from minio.error import S3Error
import os
from io import BytesIO
from django.conf import settings
from typing import List
from Backend_plants.serializers import *
from model.put_img_to_index import *
import environ
env = environ.Env()


def get_images_from_minio(plant_list: List[Plant]):
    print("plant_list", plant_list)
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_HOST,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )

    sizes = {}

    for plant in plant_list:
        img_obj_name = f"{plant.plant_name}.png"
        print("imgs_from_minio  img_obj_name =", img_obj_name)

        try:
            # Получаем объект изображения
            # response = client.stat_object(settings.AWS_STORAGE_BUCKET_NAME, img_obj_name)
            response_stat = client.stat_object(settings.AWS_STORAGE_BUCKET_NAME, img_obj_name)

        except S3Error as e:
            print(f"Ошибка доступа к изображению {img_obj_name}: {e}")
        
        # Получаем размер файла
        # size = response.size
        # image_data = BytesIO(response.read())
        size = response_stat.size

        # Получаем объект изображения
        response = client.get_object(settings.AWS_STORAGE_BUCKET_NAME, img_obj_name)

        # Читаем данные изображения
        image_data = BytesIO(response.read())
        put_img_to_index(image_data, plant.plant_name)


        sizes[plant.plant_id] = {
            'plant_name': plant.plant_name,
            'image_size': size  # Размер в байтах
        }

    # return sizes


