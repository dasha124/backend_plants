from django.utils import timezone
from django.db.models import Q
# Create your views here.
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from datetime import date
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from Backend_plants.serializers import *
from backend_plants.models import *
from rest_framework.decorators import api_view
from operator import itemgetter
# from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
import redis
import uuid
from .permissions import *
import json
from django.contrib.sessions.models import Session
from .jwt_tokens import *
from django.core.cache import cache
from base64 import b64encode
from django.core.files.base import ContentFile
import requests
from backend_plants.to_minio import *
from backend_plants.get_pic_from_minio import *
from recs.recs import *
from recs.imgs_from_minio import *
# from drf_yasg.utils import swagger_auto_schema


# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def get_session_id(request):
    session = request.COOKIES.get('session_id')
    if session is None:
        session = request.data.get('session_id')
    if session is None:
        authorization_header = request.headers.get("Authorization")
        if authorization_header and authorization_header.lower().startswith("bearer "):
            session = authorization_header[len("bearer "):]
        else:
            session = authorization_header
    return session


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def register_admin(request):
    # Ensure username and passwords are posted is properly
    serializer = AdminRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Create admin
    admin = serializer.save()
    message = {
        'сообщение': 'Админ успешно зарегистрирован',
        'admin_id': admin.admin_id
    }

    return Response(message, status=status.HTTP_201_CREATED)

#@swagger_auto_schema(method='post',request_body=UserRegisterSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def register(request):
    # Ensure username and passwords are posted is properly
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = serializer.save()
    message = {
        'сообщение': 'Пользователь успешно зарегистрирован',
        'user_id': user.user_id
    }

    return Response(message, status=status.HTTP_201_CREATED)
    

#@swagger_auto_schema(method='post',request_body=UserLoginSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    # Проверка входных данных
    serializer = UserLoginSerializer(data=request.data)
    print("req", serializer )
    if not serializer.is_valid():
        print("not valid",serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Аутентификация пользователя
    user = authenticate(request, **serializer.validated_data)
    print("проверка",user)
    if user is None:
        message = {"сообщение": "Пользователь не найден"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    # Создание токена доступа
    access_token = create_access_token(user.user_id)

    # Сохранение данных пользователя в кеше
    user_data = {
       "user_id": user.user_id,
       "user_name": user.username,
       "user_email": user.email,
       "is_superuser": user.is_superuser,
       "access_token": access_token
    }
    access_token_lifetime = settings.ACCESS_TOKEN_LIFETIME
    cache.set(access_token, user_data, access_token_lifetime)

    # Отправка ответа с данными пользователя и установкой куки
    response_data = {
        "user_id": user.user_id,
        "user_name": user.username,
        "user_email": user.email,
        "is_superuser": user.is_superuser,
        "access_token": access_token
    }
    response = HttpResponse(json.dumps(response_data), content_type="application/json")
    response.set_cookie('access_token', access_token, httponly=False, expires=access_token_lifetime, samesite=None, secure=True)

    return response
    
#@swagger_auto_schema(method='POST')
@api_view(["GET"])
@permission_classes([AllowAny])
def check(request):
    access_token = get_access_token(request)
    print("check = ", access_token)

    if access_token is None:
        message = {"message": "Token is not found"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
    if not cache.has_key(access_token):
        message = {"message": "Token is not valid"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    user_data = cache.get(access_token)
    print(user_data)
    return Response([{"user_id": user_data['user_id'], "user_name": user_data['user_name'], "user_email": user_data['user_email'], "is_superuser":user_data['is_superuser']}],status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
   
    access_token = get_access_token(request)
    print("logout = ", access_token)

    if access_token is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if cache.has_key(access_token):
        cache.delete(access_token)

    response = Response(status=status.HTTP_200_OK)
    response.delete_cookie('access_token')

    return response



@permission_classes([AllowAny])
@api_view(['GET'])
def get_plant_classes(request, format=None):
    plant_classes = Plant_Class.objects.all()
    serializer = GetPlantClassSerializer(plant_classes, many=True)
    return Response(serializer.data)


@permission_classes([AllowAny])
@api_view(['GET'])
def get_plant_subclasses(request, format=None):
    plant_subclasses = Plant_Subclass.objects.all()
    serializer = GetPlantSubclassSerializer(plant_subclasses, many=True)
    return Response(serializer.data)


@permission_classes([AllowAny])
@api_view(['GET'])
def get_plant_types(request, format=None):
    plant_types = Plant_Type.objects.all()
    serializer = GetPlantTypeSerializer(plant_types, many=True)
    return Response(serializer.data)


# список растений
@permission_classes([AllowAny])
#@swagger_auto_schema(method='GET')
@api_view(['GET'])
def get_plants(request, format=None):
    plant_name_r = request.GET.get('plant_name')
    type_name_r = request.GET.get('type_name')
    class_name_r = request.GET.get('class_name')
    light_filter = request.GET.get('light') 
    token = get_access_token(request)

    plants = Plant.objects.all().order_by('plant_name')

    print(plants[:2])

    if plant_name_r:
        print("plant_name_r =", plant_name_r)
        plants = plants.filter(
            Q(plant_name__icontains = plant_name_r.lower())
        )
    if type_name_r:
        print("type_name_r =", type_name_r)
        plant_type = get_object_or_404(Plant_Type, type_name__icontains = type_name_r)
        plants = plants.filter(plant_type = plant_type.plant_type_id)
    if class_name_r:
        print("class_name_r =", class_name_r)
        plant_class = get_object_or_404(Plant_Class, class_name = class_name_r)
        plants = plants.filter(plant_class = plant_class.plant_class_id)
    if light_filter:
        print("light_filter =", light_filter)
        plants = plants.filter(properties__light__icontains=light_filter)

    token = get_access_token(request)
    if not token:
        plants = plants.filter(Q(status='a'))
        serializer = PlantSerializer(plants, many=True)
        return Response(serializer.data)
    else:
        payload = get_jwt_payload(token)
        user_id = payload["user_id"]
        try:
            curr_user = CustomUser.objects.get(user_id= user_id)
        except CustomUser.DoesNotExist:
            curr_user = None
        try:
            admin_user = AdminUser.objects.get(admin_id = user_id)
            print("admin!!!", )
        except AdminUser.DoesNotExist:
            admin_user = None
        print("uuuuuuu", curr_user)

        if admin_user:
            pass
        else:
            plants = plants.filter(status='a')

        serializer = PlantSerializer(plants, many=True)
        return Response(serializer.data)

        

# информация о растении (услуге)
#@swagger_auto_schema(method='get')
@api_view(['GET'])
def get_plant(request, id, format=None):
    print("plant_id =", id)
    plant = get_object_or_404(Plant, plant_id=id)
    if request.method == 'GET':
        serializer = PlantSerializer(plant)
        return Response(serializer.data)

def safe_get(data_dict, key, default=None):
#  первый элемент списка по ключу или default, если ключ пуст или не существует
    return data_dict.get(key)[0] if data_dict.get(key) else default
# # добавление нового растения (услуги)
#@swagger_auto_schema(method='post',request_body=PlantSerializer)
@api_view(['POST'])
@permission_classes([IsManager])
def add_new_plant(request, format=None):
    data=request.POST
    try:
        plant = Plant.objects.get(plant_name=data['plant_name'])
        return Response({"message": "Растение с таким названием уже существует в БД"})
    
    except Plant.DoesNotExist:
        token = get_access_token(request)
        if not token:
            return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        payload = get_jwt_payload(token)
        user_id = payload["user_id"]
        print("user", user_id)

        image_file = request.FILES.get('image_url')
        image_url = image_file if image_file else None

        formatted_data = {
        'plant_name': data['plant_name'],
        'plant_class': data['plant_class'],
        'plant_subclass': data['plant_subclass'] if data['plant_subclass'] else None,  # Установим None, если пусто
        'plant_type': data['plant_type'],
        'general_info': data['general_info'],
        'properties': json.loads(data['properties']),
        }

        
        plant_class_name = data.get("plant_class")
        plant_class_id = None
        if plant_class_name:
            try:
                plant_class, created = Plant_Class.objects.get_or_create(class_name=plant_class_name)
                last_plant = Plant.objects.last()
                if last_plant is not None:
                    plant_id = getattr(last_plant, 'plant_id', None)
                    if plant_id is not None:
                        print("Последний plant_id:", plant_id)
                        formatted_data['plant_id'] = plant_id + 1
                    else:
                        print("Поле plant_id не существует в данной модели.")
                else:
                    print("Нет объектов в таблице Plant_Class.")
                plant_class_id = plant_class.plant_class_id
                formatted_data['plant_class'] = plant_class_id
                print(f"Using Plant Class - ID: {plant_class_id}, Name: {plant_class_name}")
            except Exception as e:
                print(f"Error while getting/creating Plant Class: {e}")

        plant_subclass_name = formatted_data['plant_subclass']
        print("input plant_subclass_name =", plant_subclass_name)
        plant_subclass_id = None
        if plant_subclass_name:
            try:
                if 'plant_class' in formatted_data:
                    plant_class_instance = Plant_Class.objects.get(plant_class_id=formatted_data['plant_class'])
                    plant_subclass, created = Plant_Subclass.objects.get_or_create(
                        subclass_name=plant_subclass_name,
                        plant_class=plant_class_instance
                    )
                    plant_subclass_id = plant_subclass.plant_subclass_id
                    formatted_data['plant_subclass'] = int(plant_subclass_id)
                    print(f"Plant Subclass - ID: {plant_subclass_id}, Name: {plant_subclass_name}")
                else:
                    print("Plant class не определен, нельзя создать subclass.")
            except Exception as e:
                print(f"Ошибка получения/создания Plant Subclass: {e}")
        
        plant_type_name = formatted_data.get("plant_type")
        plant_type_id = None
        if plant_type_name:
            try:
                plant_type, created = Plant_Type.objects.get_or_create(type_name=plant_type_name, plant_subclass_id=plant_subclass_id)
                plant_type_id = plant_type.plant_type_id
                formatted_data['plant_type'] = plant_type_id
                print(f"Using Plant Type - ID: {plant_type_id}, Name: {plant_type_name}")
            except Exception as e:
                print(f"Error while getting/creating Plant Type: {e}")

        final_data = {
        'plant_id': formatted_data.get('plant_id'),  # Сначала добавим plant_id
        }
        final_data.update(formatted_data)

        serializer = GetPlantSerializer(data=final_data)
        print("serial 0 =", serializer)
        if serializer.is_valid():
            new_plant_instance = serializer.save()
            pic_result = add_pic(new_plant_instance, image_file)
            last_plant = Plant.objects.last()
            plant_id_new = getattr(last_plant, 'plant_id', None)
            admin_user = AdminUser.objects.get(user_id=user_id)
            interaction = Interaction.objects.create(action_id=1, plant_id=plant_id_new, admin=admin_user)
            interaction.save()  
            return Response({"message": "Растение успешно добавлено в БД"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# # обновление информации о заболевании (услуге)
# #@swagger_auto_schema(method='put', request_body=PlantSerializer)
@api_view(['PUT'])
@permission_classes([IsManager])
@authentication_classes([])
def update_plant(request, id, format=None):

    data=request.POST
    try:
        plant = Plant.objects.get(plant_id=id)
        print("изначальное растение: ", plant)
         # Обновление других полей растения
    except Plant.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    print("user", user_id)

    image_file = request.FILES.get('image_url')

    final_data = {
        'plant_id': id,
        'plant_name': data['plant_name'],
        'plant_class': data['plant_class'],
        'plant_subclass': data['plant_subclass'] if data['plant_subclass'] else None,  # Установим None, если пусто
        'plant_type': data['plant_type'],
        'general_info': data['general_info'], 
        'properties': json.loads(data['properties']),
    }
    plant_class_name = data.get("plant_class")
    plant_class_id = None
    if plant_class_name:
        try:
            plant_class, created = Plant_Class.objects.get_or_create(class_name=plant_class_name)
            
            plant_class_id = plant_class.plant_class_id
            final_data['plant_class'] = plant_class_id
            print(f"Using Plant Class - ID: {plant_class_id}, Name: {plant_class_name}")
        except Exception as e:
            print(f"Error while getting/creating Plant Class: {e}")
    # print("data ser 1",data)
    # Process plant subclass
    plant_subclass_name = final_data.get("plant_subclass")
    plant_subclass_id = None
    if plant_subclass_name:
        try:
            plant_subclass, created = Plant_Subclass.objects.get_or_create(subclass_name=plant_subclass_name, plant_class_id = final_data['plant_class'])
            plant_subclass_id = plant_subclass.plant_subclass_id
            final_data['plant_subclass'] = plant_subclass_id
            print(f"Using Plant Subclass - ID: {plant_subclass_id}, Name: {plant_subclass_name}")
        except Exception as e:
            print(f"Error while getting/creating Plant Subclass: {e}")
        
    plant_type_name = final_data.get("plant_type")
    plant_type_id = None
    if plant_type_name:
        try:
            plant_type, created = Plant_Type.objects.get_or_create(type_name=plant_type_name, plant_subclass_id=final_data['plant_subclass'])
            plant_type_id = plant_type.plant_type_id
            final_data['plant_type'] = plant_type_id
            print(f"Using Plant Type - ID: {plant_type_id}, Name: {plant_type_name}")
        except Exception as e:
            print(f"Error while getting/creating Plant Type: {e}")

    serializer = GetPlantSerializer(instance=plant, data=final_data, partial=True)
    print("serial 0 =", serializer)
    if serializer.is_valid():
        # serializer.save()
        new_plant_instance = serializer.save()
        # print("new_plant_instance =", type(new_plant_instance))
        pic_result = add_pic(new_plant_instance, image_file)

        plant_id_new = final_data.get('plant_id')
        admin_user = AdminUser.objects.get(admin_id=user_id)
        interaction = Interaction.objects.create(action_id=2, plant_id=plant_id_new, admin=admin_user)
        interaction.save()  
        return Response({"message": "Растение успешно обновлено в БД"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# удаление информации о растении
@api_view(['DELETE'])
@permission_classes([IsManager])
@authentication_classes([])
def delete_plant(request, id, format=None):
    print('delete', id)
    try:
        plant = Plant.objects.get(plant_id=id)
        # print("изначальное растение: ", plant)
        # Обновление других полей растения
    except Plant.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    print("user", user_id)

    plant.status="d"
    plant.save()
    admin_user = AdminUser.objects.get(admin_id=user_id)
    interaction = Interaction.objects.create(action_id=3, plant_id=id, admin=admin_user)
    interaction.save()  
    return Response({"message": "Растение имеет статус 'd = deleted'"}, status=status.HTTP_204_NO_CONTENT)



# # # удаление информации о растении (услуге)
# @api_view(['DELETE'])
# @permission_classes([IsManager])
# @authentication_classes([])
# def obj_delete_plant(request, id, format=None):
#     print('delete', id)
#     try:
#         plant = Plant.objects.get(plant_id=id)
#     except Plant.DoesNotExist:
#         return Response(f"Растение {id} не найдено в Базе данных", status=status.HTTP_404_NOT_FOUND)

#     token = get_access_token(request)
#     if not token:
#         return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
#     payload = get_jwt_payload(token)
#     user_id = payload["user_id"]
#     print("user", user_id)

#     plant.delete()
#     return Response(f"Растение {id} удалено из Базы данных", status=status.HTTP_204_NO_CONTENT)


# # добавление услуги в заявку
# #@swagger_auto_schema(method='post', request_body=PlantSerializer)
@api_view(['POST'])
@permission_classes([IsUser])
def add_plant_to_collection(request, id_plant, id_coll):
    # print("add pl to coll", id)

    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    # print("user", user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    if not Plant.objects.filter(plant_id=id_plant).exists():
        return Response({"error": "Растения с таким id не найдено"}, status=status.HTTP_404_NOT_FOUND)
    
    plant = Plant.objects.get(plant_id=id_plant)
    try:
        collection = Collection.objects.get(collection_id=id_coll, user=user_id)
        collection_id = collection.collection_id
        # return Response({"error": "Растение уже в черновой коллекции"})
    except Collection.DoesNotExist:
        collection = Collection.objects.create(user=user)
        collection.collection_name = "Название коллекции"
        collection_id = collection.collection_id
        collection.save()


    try:
        plant_in_col = CollectionPlant.objects.get(collection_id=collection_id, plant_id=id_plant)
        return Response({"error": "Растение уже в черновой коллекции"})
    except CollectionPlant.DoesNotExist:
        plant_in_col = CollectionPlant.objects.create(collection_id=collection_id, plant_id=id_plant)

        
    collection.includes_plants.add(plant)
    collection.save()

    # serializer = CollectionPlantSerializer(plant_in_col)
    col_serializer = CollectionsSerializer(collection, many=False)
    # return Response(col_serializer.data)
    return Response({"message": "Растение добавлено в коллекцию", "collection": col_serializer.data}, status=status.HTTP_200_OK)
    

# #@swagger_auto_schema(method='get')
@api_view(['GET'])
@permission_classes([IsUser])
def get_collections(request, format=None):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, "user_id =", user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    collection_name_r = request.GET.get('collection_name') ## поиск коллекции по названию
    # time_create= request.GET.get('time_create')
    status_r= request.GET.get('status') ## фильтрация по статусу


    collections= Collection.objects.order_by('-time_create').filter(user=user_id, status=1)
    if collection_name_r:
        collections = collections.filter(
            Q(collection_name__icontains = collection_name_r.lower())
        )
    if status_r is not None:
        collections = collections.filter(
            Q(status = status_r)
        )

    serializer = CollectionsSerializer(collections, many=True)
    return Response(serializer.data)



# #@swagger_auto_schema(method='get')
@api_view(['GET'])
@permission_classes([IsUser])
def get_collection(request, id, format=None):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    
    try:
        collection = Collection.objects.get(collection_id=id)
    except Collection.DoesNotExist:
        return Response(f"Коллекция с id={id} не найдена", status=status.HTTP_404_NOT_FOUND)
    serializer = CollectionsSerializer(collection)

    if collection.user == user:
        return Response(serializer.data)
    else:
        return Response("Нет доступа к данным")


@api_view(['POST'])
@permission_classes([IsUser])
def create_collection(request, format=None):

    token = get_access_token(request)
    if not token:
        return Response({"Нет токена"}, status=status.HTTP_401_UNAUTHORIZED)
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    curr_user = CustomUser.objects.get(user_id = user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    data=request.data

    collection = Collection.objects.create(user=user)
    collection.collection_name = data['collection_name']
    collection.save()

    return Response({"collection_id": collection.collection_id, "collection_name": collection.collection_name}, 
                    status=status.HTTP_201_CREATED)



@api_view(['DELETE'])
@permission_classes([IsUser])
def delete_collection(request, id, format=None):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    try:
        collection = Collection.objects.get(collection_id=id)
    except Collection.DoesNotExist:
        return Response(f"Коллекция с id={id} не найдена", status=status.HTTP_404_NOT_FOUND)

    if collection.user == user:
        collection.status = 2
        collection.save()
        return Response(f"Коллекция с id={id} успешно удалена", status=status.HTTP_200_OK)
    else:
        return Response("Нет доступа к данным коллекции")

    

# # удаление растения из связанной с ним коллекции (из м-м)
@api_view(['DELETE'])
@permission_classes([IsUser])
def delete_plant_from_collection(request, id_collection, id_plant, format=None):
    
    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)
    
    if not Collection.objects.filter(collection_id=id_collection).exists():
        return Response(f"Коллекции с таким id не существует")
    if not Plant.objects.filter(plant_id=id_plant).exists():
        return Response(f"Растения с таким id не существует")
    
    
    plant = Plant.objects.get(plant_id=id_plant)
    print("plant =", plant)
    collection = Collection.objects.get(collection_id=id_collection)
    print("collection =", collection)
    if collection.includes_plants.exists():
        collection.includes_plants.remove(plant)
        collection.save()
        return Response(f"Удаление выбранного растения из коллекции выполнено")
    else:
        return Response(f"Объекта выбранного растения для удаления из коллекции не найдено", status = status.HTTP_404_NOT_FOUND)
    



@api_view(['PUT'])
@permission_classes([IsUser])
def collection_upd_status_to_created_from_del(request, id):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    if not Collection.objects.filter(user=user, status=2).exists():
        return Response(f"Удаленных коллекций для пользователя {user} не существует")
    
    try:
        collection = Collection.objects.get(user=user, collection_id=id, status=2)
    except Collection.DoesNotExist:
        return Response(f"Ошибка восстановления коллекции {id} для пользователя {user}")
    collection.status = 1
    collection.save()
    return Response(f'Успешно обновлен статус коллекции на "Сформирован" для пользователя {user}', status=status.HTTP_200_OK)


 
@api_view(['PUT'])
@permission_classes([IsUser])
def update_collection(request, id):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')

    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    try:
        collection = Collection.objects.get(user=user, collection_id=id)
    except Collection.DoesNotExist:
        return Response(f"Коллекции c id={id} для пользователя {user} не существует", status=status.HTTP_404_NOT_FOUND)

    data=request.data

    collection.collection_name = data['collection_name']
    collection.save()
    serializer = CollectionSerializer(collection)

    return Response(serializer.data, status=status.HTTP_200_OK)



# @permission_classes([IsUser])
@api_view(['DELETE'])
def del_recommendation(request, id, format=None):
    recommendation = get_object_or_404(Recommendation, recommendation_id=id)
    recommendation.delete()
    return Response(f"Рекомендация {id} удалена из Базы данных", status=status.HTTP_204_NO_CONTENT)
            

# здесь пока что фотка начального растения - в топе 1 по похожести, ее надо убрать
@api_view(['GET'])
def get_recommendation_by_plant(request, id_plant, format=None):
    with open('recs/index_1.json', 'rb') as f:
        index = json.load(f) 
    with open('recs/vects_1.npy', 'rb') as f:
        vects = np.load(f)  
        

    print("##################################################################################################################################")   
    print(index)
    print("##################################################################################################################################")   
    # id_plant - id из бд
    id_plant0 = id_plant
    plant_name = get_object_or_404(Plant, plant_id=id_plant).plant_name
    print("plant_name =", plant_name)
    try:
        id_plant = index.index(plant_name)
        print("id_plant in INDEX =", id_plant)
    except ValueError:
        print("Замена названия на дефолт!!!!!!")
        id_plant = index.index('Бархатцы французские')

    viewed_ids = [id_plant]
    print("viewed_ids = [id_plant] =", viewed_ids)
    res = get_sim_mean(viewed_ids, vects)
    res_ids = res['similar_ind']
    similar_ids = list(map(int, res['similar_ind']))
    output_len = len(similar_ids)

    try: 
        recommendation = Recommendation.objects.get(plant=id_plant0)

        if recommendation:
            RecommendationPlant.objects.filter(recommendation_id = recommendation).delete()
            # serializer = RecommendationSerializer(recommendation)
            # return Response(serializer.data, status=status.HTTP_200_OK)
            for rec_plant_id in similar_ids:
                ind_plant_name = index[rec_plant_id]
                print("rec_plant_id = ", rec_plant_id, "index[rec_plant_id] = ", index[rec_plant_id], ind_plant_name)
                plant = get_object_or_404(Plant, plant_name = ind_plant_name)
                print(plant)
                if plant.status=="a":
                    print("a =", plant, plant.plant_id)
                    RecommendationPlant.objects.create(recommendation=recommendation, plant=plant, weight=output_len)
                    output_len -= 1
                else:
                    print("d =", plant, plant.plant_id)
            
            serializer = RecommendationForPlantSerializer(recommendation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Recommendation.DoesNotExist:
        new_rec = Recommendation.objects.create(plant_id=id_plant0, collection=None)
        print("Recommendation.DoesNotExist similar_ids =", similar_ids)
        for rec_plant_id in similar_ids:

            ind_plant_name = index[rec_plant_id]
            print("rec_plant_id = ", rec_plant_id, "index[rec_plant_id] = ", index[rec_plant_id], ind_plant_name)
            plant = get_object_or_404(Plant, plant_name = ind_plant_name)
            if plant.status=="a":
                print("a =", plant, plant, plant.plant_id)
                RecommendationPlant.objects.create(recommendation=new_rec, plant=plant, weight=output_len)
                output_len -=1
            else:
                print("d =", plant, plant.plant_id)
            
        serializer = RecommendationForPlantSerializer(new_rec)
        return Response(serializer.data, status=status.HTTP_201_CREATED)





@api_view(['GET'])
@permission_classes([IsUser])
def get_recommendation_by_coll(request, id_coll, format=None):

    token = get_access_token(request)
    if not token:
        return Response('Нет токена')
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    user = get_object_or_404(CustomUser, user_id=user_id)

    with open('recs/index_1.json', 'rb') as f:
        index = json.load(f) 
    with open('recs/vects_1.npy', 'rb') as f:
        vects = np.load(f)
    
    collection = Collection.objects.get(collection_id=id_coll, user=user_id)
    plant_ids = collection.includes_plants.values_list('plant_id', flat=True)
    plant_ids_list = list(plant_ids)
    print(plant_ids_list)

    ids = []
    for id in plant_ids_list:
        plant_name = get_object_or_404(Plant, plant_id=id).plant_name
        try:
            id_plant = index.index(plant_name)
        except ValueError:
            print("Замена названия на дефолт!!!!!!")
            id_plant = index.index('Бархатцы французские')
        ids.append(id_plant)
    print("ids =", ids)

    viewed_ids = ids
    res = get_sim_mean(viewed_ids, vects)
    similar_ids = list(map(int, res['similar_ind']))
    output_len = len(similar_ids)

    try:
        recommendation = Recommendation.objects.get(collection=id_coll, user=user_id)
        print("Рекомендация сущесвтует")
        if recommendation:
            RecommendationPlant.objects.filter(recommendation_id = recommendation).delete()
            
            for rec_plant_id in similar_ids:
                ind_plant_name = index[rec_plant_id]
                plant = get_object_or_404(Plant, plant_name = ind_plant_name)
                print(plant)
                if plant.status=="a":
                    print("a =", plant, plant.plant_id)
                    RecommendationPlant.objects.create(recommendation=recommendation, plant=plant, weight=output_len)
                    output_len -= 1
                else:
                    print("d =", plant, plant.plant_id)
            
            serializer = RecommendationForCollectionSerializer(recommendation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Recommendation.DoesNotExist:
        new_rec = Recommendation.objects.create(plant=None, collection_id=id_coll, user_id=user.user_id)
        
        for rec_plant_id in similar_ids:
            ind_plant_name = index[rec_plant_id]
            print("rec_plant_id = ", rec_plant_id, "index[rec_plant_id] = ", index[rec_plant_id], ind_plant_name)
            plant = get_object_or_404(Plant, plant_name = ind_plant_name)
            if plant.status=="a":
                print("a =", plant, plant, plant.plant_id)
                RecommendationPlant.objects.create(recommendation=new_rec, plant=plant, weight=output_len)
                output_len -=1
            else:
                print("d =", plant, plant.plant_id)
            
        serializer = RecommendationForCollectionSerializer(new_rec)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


        
        
        
        
        pass
        # создаем рекомендацию по коллекции

    # collection = get_object_or_404(Collection, collection_id=id_coll)
    try:
        collection = Collection.objects.get(collection_id=id_coll)
        collection.delete()
    except Collection.DoesNotExist:
        return Response(f"Коллекции с {id_coll} не найдено в Базе данных", status=status.HTTP_404_NOT_FOUND)

    


@permission_classes([AllowAny])
@api_view(['GET'])
def get_recommendation_by_Expert(request, format=None):
    plants= Plant.objects.all()
    serializer = GetPlantSerializer(plants, many=True)
    return Response(serializer.data)

# #@swagger_auto_schema(method='get')
# @api_view(['GET'])
# # @permission_classes([AllowAny])
# # @authentication_classes([BasicAuthentication])

#выводит ВСЕХ юзиков, в том числе админов
@api_view(['GET'])
def get_user(request,id, format=None):
    user = CustomUser.objects.get(user_id = id)
    return Response([{"user_id": user.user_id, "user_name": user.username, "user_email": user.email, "is_superuser": user.is_superuser}],status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsManager])
@authentication_classes([])
def obj_delete_user(request, id, format=None):
    print('delete', id)
    try:
        user = CustomUser.objects.get(user_id=id)
    except CustomUser.DoesNotExist:
        return Response(f"Пользователя с {id} не найдено в Базе данных", status=status.HTTP_404_NOT_FOUND)

    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    print("user", user_id)

    user.delete()
    return Response(f"Пользователь {id} удален из Базы данных", status=status.HTTP_204_NO_CONTENT)


# Пример использования:
@api_view(['GET'])
def get_image_sizes_from_minio(request, format=None):
    # plant_list = Plant.objects.filter(plant_id__in = [1, 2])
    plant_list = Plant.objects.all().order_by('plant_name')
    print(plant_list)
    # sizes = get_image_sizes(plant_list)
    sizes = get_images_from_minio(plant_list)
    # print(sizes)
    return Response(len(sizes))