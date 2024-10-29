from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from Backend_plants.serializers import *

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    print("//process_file_upload")
    print("file_object =", file_object, type(file_object))
    print("client = ", client)
    print("image_name =", image_name, type(image_name))
    print("Объем файла:", file_object.size)
    try:
        client.put_object('logo', image_name, file_object, file_object.size)
        return f"http://localhost:9000/logo/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_plant: Plant, pic):
    client = Minio(           
            endpoint=settings.AWS_S3_ENDPOINT_URL,
           access_key=settings.AWS_ACCESS_KEY_ID,
           secret_key=settings.AWS_SECRET_ACCESS_KEY,
           secure=settings.MINIO_USE_SSL
    )
    print("minio new plant", new_plant)
    
    
    i = new_plant.plant_id
    # i = data.plant_id
    # print("i =", type(i))
    img_obj_name = f"{i}.png"
    print("pic=", type(pic))
    print("img_obj_name =", img_obj_name)

    if not pic:
        return Response({"error": "Нет файла для изображения."})
    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        print("error in res")
        return Response(result)

    new_plant.image_url = result
    new_plant.save()
    print("result  =", result)

    return Response({"message": "success"})
    # return result