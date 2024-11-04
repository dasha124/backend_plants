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
from backend_plants.minio import *
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
@api_view(["POST"])
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
    return Response(user_data, status=status.HTTP_200_OK)


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




# список растений (услуг)
@permission_classes([AllowAny])
#@swagger_auto_schema(method='GET')
@api_view(['GET'])
def get_plants(request, format=None):
    plant_name_r = request.GET.get('plant_name')
    collectionID = 0
    token = get_access_token(request)
    # print("ищем токен ----", token, type(token))
    if token not in ['undefined', 'None']:
    # if token !=None:
        payload = get_jwt_payload(token)
        user_id = payload["user_id"]

        try:
            curr_user = CustomUser.objects.get(user_id= user_id)
        except CustomUser.DoesNotExist:
            curr_user = None
        try:
            admin_user = AdminUser.objects.get(admin_id = user_id)
        except AdminUser.DoesNotExist:
            admin_user = None
        print("uuuuuuu", curr_user)


        # try {        #     drug = Medical_drug.objects.get(user_id_id=user_id, status=0)
        if admin_user:
            print("curr_user.is_superuser")
            if plant_name_r:
                plants = Plant.objects.filter(
                    Q(plant_name__icontains = plant_name_r.lower())
                )       
            else:
                plants = Plant.objects.all()
                print(plants)
            collectionID = 0 # так то коллекций у админов нет
        # if not admin_user:
        else:
            try:
                collection = Collection.objects.get(user_id=user_id, status=0)
                collectionID = collection.collection_id
            except Collection.DoesNotExist:
                collectionID = 0

            if plant_name_r:
                plants = Plant.objects.filter(
                    Q(status='a') &
                    Q(plant_name__icontains = plant_name_r.lower())
                )
            else:
                plants = Plant.objects.filter(
                    Q(status='a')
                )

        serialized_plants = []
        for plant in plants:
            serializer = PlantSerializer(plant)
            serialized_plants.append(serializer.data)
        serialized_plants.append({"collectionID": collectionID})

        return Response(serialized_plants)
    # if token == 'undefined':
    else:
        collectionID=0
        print('here')
        if plant_name_r: # TODO
            plants = Plant.objects.filter(
                Q(status='a') &
                Q(plant_name__icontains = plant_name_r.lower())
            )
            
            serialized_plants = []
            for plant in plants:
                serializer = PlantSerializer(plant)
                serialized_plants.append(serializer.data)

            serialized_plants.append({"collectionID": 0})

            return Response(serialized_plants)

        
        plants = Plant.objects.filter(
        Q(status='a')
        )

        serialized_plants = []
        for plant in plants:
            serializer = PlantSerializer(plant)
            serialized_plants.append(serializer.data)

        serialized_plants.append({"collectionID": 0})

        return Response(serialized_plants)


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
# """Возвращает первый элемент списка по ключу или default, если ключ пуст или не существует."""
    return data_dict.get(key)[0] if data_dict.get(key) else default
# # добавление нового растения (услуги)
#@swagger_auto_schema(method='post',request_body=PlantSerializer)
@api_view(['POST'])
@permission_classes([IsManager])
def add_new_plant(request, format=None):
    # print("request user =", request.user, request.user.id)
    data=request.POST
    try:
        plant = Plant.objects.get(plant_name=data['plant_name'])
        # plant = get_object_or_404(Plant, plant_name=data['plant_name'])
        return Response({"message": "Растение с таким названием уже существует в БД"})
    
    except Plant.DoesNotExist:
        token = get_access_token(request)
        if not token:
            return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        payload = get_jwt_payload(token)
        user_id = payload["user_id"]
        print("user", user_id)

        # print("data ser 0",data)
        image_file = request.FILES.get('image_url')
        image_url = image_file if image_file else None
        # print("img url =", type(image_url))

        formatted_data = {
        'plant_name': data['plant_name'],  # Получаем первое значение
        'plant_class': data['plant_class'],  # Приводим к int
        'plant_subclass': (data['plant_subclass'], None) if data['plant_subclass'] else None,  # Установим None, если пусто
        'general_info': data['general_info'], 
        'properties': json.loads(data['properties']),
        }

        
        # Process plant class
        plant_class_name = data.get("plant_class")
        plant_class_id = None
        if plant_class_name:
            try:
                plant_class, created = Plant_Class.objects.get_or_create(class_name=plant_class_name)
                last_plant = Plant.objects.last()
                if last_plant is not None:
                # Проверяем, существует ли plant_id в этом объекте
                    plant_id = getattr(last_plant, 'plant_id', None)  # безопасно добавить возможность вернуть None
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
        # print("data ser 1",data)
        # Process plant subclass
        plant_subclass_name = formatted_data.get("plant_subclass")
        plant_subclass_id = None
        if plant_subclass_name:
            try:
                plant_subclass, created = Plant_Subclass.objects.get_or_create(subclass_name=plant_subclass_name)
                plant_subclass_id = plant_subclass.plant_subclass_id
                formatted_data['plant_subclass'] = plant_subclass_id
                print(f"Using Plant Subclass - ID: {plant_subclass_id}, Name: {plant_subclass_name}")
            except Exception as e:
                print(f"Error while getting/creating Plant Subclass: {e}")

        final_data = {
        'plant_id': formatted_data.get('plant_id'),  # Сначала добавим plant_id
        }
        final_data.update(formatted_data)


        serializer = PlantSerializer(data=final_data)
        # print("serial 0 =", serializer)
        if serializer.is_valid():
            # serializer.save()
            new_plant_instance = serializer.save()
            # print("new_plant_instance =", type(new_plant_instance))
            pic_result = add_pic(new_plant_instance, image_file)

            # if 'error' in pic_result.data:
            #     print("ERRRRRR")    
            #     return pic_result  
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
            # print("ERRRRRR")
            plant_id_new = final_data.get('plant_id')
            admin_user = AdminUser.objects.get(admin_id=user_id)
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
        'plant_id': id,  # Получаем первое значение
        'plant_name': data['plant_name'],  # Получаем первое значение
        'plant_class': data['plant_class'],  # Приводим к int
        'plant_subclass': (data['plant_subclass'], None) if data['plant_subclass'] else None,  # Установим None, если пусто
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
            plant_subclass, created = Plant_Subclass.objects.get_or_create(subclass_name=plant_subclass_name)
            plant_subclass_id = plant_subclass.plant_subclass_id
            final_data['plant_subclass'] = plant_subclass_id
            print(f"Using Plant Subclass - ID: {plant_subclass_id}, Name: {plant_subclass_name}")
        except Exception as e:
            print(f"Error while getting/creating Plant Subclass: {e}")


    serializer = PlantSerializer(instance=plant, data=final_data, partial=True)
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


# # удаление информации о заболевании (услуге)
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
    # print(f"################---------   delete_plant --- plant {plant.plant_id}   ----- by moderator { request.user}")
    admin_user = AdminUser.objects.get(admin_id=user_id)
    interaction = Interaction.objects.create(action_id=3, plant_id=id, admin=admin_user)
    interaction.save()  
    # return Response({"message": "Растение успешно обновлено в БД"}, status=status.HTTP_201_CREATED)
    return Response({"message": "Растение имеет статус 'd = deleted'"}, status=status.HTTP_204_NO_CONTENT)


# # добавление услуги в заявку
# #@swagger_auto_schema(method='post', request_body=PlantSerializer)
@api_view(['POST'])
@permission_classes([IsUser])
def add_plant_to_collection(request, id):
    # print("add pl to coll", id)

    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    # print("user", user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    if not Plant.objects.filter(plant_id=id, status='a').exists():
        return Response({"error": "Растения с таким id не найдено"}, status=status.HTTP_404_NOT_FOUND)
    
    plant = Plant.objects.get(plant_id=id)
    try:
        collection = Collection.objects.get(status=0, user=user_id)
        collection_id = collection.collection_id
        # return Response({"error": "Растение уже в черновой коллекции"})
    except Collection.DoesNotExist:
        collection = Collection.objects.create(user=user)
        collection.collection_name = "Название коллекции"
        collection_id = collection.collection_id
        recommendation_1 = Recommendation.objects.create()
        # recommendation_id = recommendation_1.recommendation_id
        collection.recommendation = recommendation_1
        collection.save()


    try:
        plant_in_col = CollectionPlant.objects.get(collection_id=collection_id, plant_id=id)
        return Response({"error": "Растение уже в черновой коллекции"})
    except CollectionPlant.DoesNotExist:
        plant_in_col = CollectionPlant.objects.create(collection_id=collection_id, plant_id=id)

        
    collection.includes_plants.add(plant)
    collection.save()

    serializer = CollectionPlantSerializer(plant_in_col)
    return Response({"message": "Растение добавлено в черновую коллекцию", "collection": serializer.data}, status=status.HTTP_200_OK)
    

# # список препаратов (заявок)
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
    print("cccccccccccurrr uuser =", curr_user)
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


@api_view(['GET'])
@permission_classes([IsUser])
def get_deleted_collections(request, format=None):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user)
    user = get_object_or_404(CustomUser, user_id=user_id)

    collection_name_r = request.GET.get('collection_name') ## поиск коллекции по названию
    # time_create= request.GET.get('time_create')
    status_r= request.GET.get('status') ## фильтрация по статусу


    collections= Collection.objects.order_by('-time_create').filter(user=user_id, status=2)
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

# # информация о препарате (заявке)
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
    serializer = CollectionSerializer(collection)

    if collection.user == user:
        return Response(serializer.data)
    else:
        return Response("Нет доступа к данным")


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
    

# # удаление коллекции-черновика (заявки)
@api_view(['DELETE'])
@permission_classes([IsUser])
def delete_editing_collection(request, format=None):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    if not Collection.objects.filter(status=0).exists():
        return Response(f"Коллекции со статусом 'Черновик' не существует")
    
    try:
        editing_collection = Collection.objects.get(status=0, user=user)
    except Collection.DoesNotExist:
        return Response(f"Коллекции со статусом 'Черновик' для пользователя {user} не существует")
    
    editing_collection.status=2
    editing_collection.save()
    editing_collection.includes_plants.clear()
    # serializer = CollectionSerializer(editing_collection, many=False)
    # return Response(serializer.data)
    return Response(f"Коллекция со статусом 'Черновик' для пользователя {user} удалена")


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
    

# #@swagger_auto_schema(method='put', request_body=CollectionSerializer)
@api_view(['PUT'])
@permission_classes([IsUser])
def collection_upd_status_to_created(request):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("cccccccccccurrr uuser =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    if not Collection.objects.filter(user=user, status=0).exists():
        return Response(f"Коллекции-черновика для пользователя {user} не существует")
    
    collection = Collection.objects.get(user=user, status=0)
    collection.status = 1
    collection.save()
    return Response(f'Успешно обновлен статус коллекции на "Сформирован" для пользователя {user}', status=status.HTTP_200_OK)


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


# #@swagger_auto_schema(method='put', request_body=CollectionSerializer)
@api_view(['PUT'])
@permission_classes([IsUser])
def collection_upd_status_to_editing(request, id):
    
    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id = user_id)
    print("curr user =", curr_user, user_id)
    user = get_object_or_404(CustomUser, user_id=user_id)

    if not Collection.objects.filter(collection_id=id, user=user, status=1).exists():
        return Response(f"Активной коллекции с таким id не существует для пользователя {user}")
    if not Collection.objects.filter(collection_id=id, user=user, status=0).exists():
        return Response(f"Удаленной коллекции с таким id не существует для пользователя {user}")
    else:
        try: 
            collection_0 = Collection.objects.get(collection_id=id, user=user, status=0)
        except Collection.DoesNotExist:
            collection = Collection.objects.get(collection_id=id, user=user)
            collection.status=0
            collection.save()
            return Response(f'Успешно обновлен статус коллекции {id} на "Черновик" для пользователя {user}', status=status.HTTP_200_OK)
        # если есть какая то-коллекция-черновик, то мы ее переводим в сформированную,
        # а коллекцию с пришедшим id переводим по команде на редактирование
        collection_0.status = 1
        collection_0.save()
        collection = Collection.objects.get(collection_id=id, user=user)
        collection.status = 0
        collection.save()
        return Response(f'Успешно обновлен статус коллекции {id} на "Черновик" для пользователя {user}', status=status.HTTP_200_OK)

 
@api_view(['POST'])
@permission_classes([IsUser])
def update_collection(request, id):

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
        collection = Collection.objects.get(user=user, collection_id=id)
        print("Изначальная коллекция: ")
        print(collection)
        print()
    except Collection.DoesNotExist:
        return Response(f"Коллекции c id={id} для пользователя {user} не существует", status=status.HTTP_404_NOT_FOUND)
    
    data=request.POST
    image_file = request.FILES.get('image_url')

    final_data = {
        'collection_id': id,  # Получаем первое значение
        'collection_name': data['collection_name'],  # Получаем первое значение
    }
    serializer = CollectionSerializer(instance=collection, data=final_data, partial=True)
    print("serial 0 =", serializer)
    if serializer.is_valid():
        # serializer.save()
        new_coll_instance = serializer.save()
        # print("new_plant_instance =", type(new_plant_instance))
        pic_result = add_pic_coll(new_coll_instance, image_file)
        return Response({"message": "Растение успешно обновлено в БД"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 

# #@swagger_auto_schema(method='get')
@api_view(['GET'])
@permission_classes([IsUser])
def get_recommendation(request, id, format=None):
    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(user_id= user_id)
    print("cccccccccccurrr uuser =", curr_user)

    recommendation = get_object_or_404(Recommendation, recommendation_id=id)
    serializer = RecommendationSerializer(recommendation)

    if not curr_user.is_superuser:
        if recommendation:
            # Здесь вставить алгоритм для построения рекомендаций
            # на основе карточек растений в collection.includes_plants
            # Например, если у вас есть список всех растений в коллекции:
            # collection = Collection.objects.get(user_id=user_id, recomendation = id_rec)
            # recommended_plants = algorithm_to_get_recommendations(collection.includes_plants.all())

                    # Здесь добавляем растения с id = 1 и 2 пока по умолчанию, потом добавим мл по рекомендашкам сюда
            default_plants = Plant.objects.filter(plant_id__in=[1, 81, 82, 83])
            base_weight = len(default_plants)
            for index, plant in enumerate(default_plants):
                weight = base_weight - index
                recommendation_plant = RecommendationPlant(recommendation=recommendation, plant=plant, weight=weight)
                recommendation_plant.save()

            serializer = RecommendationSerializer(recommendation)
            return Response(serializer.data)
        else:
            return Response("Нет данных по коллекции для формирования рекомендаций")
    else:
        return Response("Нет доступа к данным")
            


# #@swagger_auto_schema(method='get')
# @api_view(['GET'])
# # @permission_classes([AllowAny])
# # @authentication_classes([BasicAuthentication])

#выводит ВСЕХ юзиков, в том числе админов
@api_view(['GET'])
def get_users(request,format=None):
    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_admins(request,format=None):
    admins = AdminUser.objects.all()
    serializer = AdminSerializer(admins, many=True)
    print(serializer)
    return Response(serializer.data)



# #@swagger_auto_schema(method='put', request_body=DrugSerializer)
# @api_view(['PUT'])
# @permission_classes([IsManager])
# @authentication_classes([])
# def drug_update_status_admin(request, id):
#     if not Medical_drug.objects.filter(id=id).exists():
#         return Response(f"Препарата с таким id не существует")
    
#     STATUSES = [0, 1, 2, 3, 4]
#     request_st = request.data["status"]

#     if request_st not in STATUSES:
#         return Response("Статус не корректен")
    
#     drug = Medical_drug.objects.get(id=id)
#     drug_st = drug.status
#     print("drug_st =", drug_st)

#     if request_st == 2 or request_st == 3:
#         drug.status = request_st
#         drug.save()

#         serializer = DrugSerializer(drug, many=False)
#         return Response(serializer.data)
#     else:
#         return Response("Изменение статуса невозможно")





# #@swagger_auto_schema(method='put')
# @api_view(['PUT'])
# @permission_classes([AllowAny])
# def async_result(request, format=None):
#     try:
#         # Преобразуем строку в объект Python JSON
#         json_data = json.loads(request.body.decode('utf-8'))
#         print(json_data)
#         const_token = 'my_secret_token'

#         if const_token != json_data['token']:
#             return Response(data={'message': 'Ошибка, токен не соответствует'}, status=status.HTTP_403_FORBIDDEN)

       
#         try:
#             # Выводит конкретную заявку создателя
#             drug = get_object_or_404(Medical_drug, id=json_data['id_test'])
#             drug.test_status = json_data['test_status']
          
#             drug.save()
#             data_json = {
#                 'id': drug.id,
#                 'test_status': drug.get_test_status_display_word(),
#                 'status': drug.get_grug_display_word()
#             }
#             return Response(data={'message': 'Статус тестированя успешно обновлен', 'data': data_json},
#                             status=status.HTTP_200_OK)
#         except ValueError:
#             return Response({'message': 'Недопустимый формат преобразования'}, status=status.HTTP_400_BAD_REQUEST)
#     except json.JSONDecodeError as e:
#         print(f'Error decoding JSON: {e}')
#         return Response(data={'message': 'Ошибка декодирования JSON'}, status=status.HTTP_400_BAD_REQUEST)
    
