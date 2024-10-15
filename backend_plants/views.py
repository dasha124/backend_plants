from django.utils import timezone
from django.db.models import Q
# Create your views here.
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from datetime import date
from django.db import connection
from django.http import JsonResponse

from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from Backend_plants.serializers import *
from backend_plants.models import *
from rest_framework.decorators import api_view
from operator import itemgetter
# from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
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
# from drf_yasg.utils import swagger_auto_schema

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
        'message': 'Пользователь успешно зарегистрирован',
        'user_id': user.id
    }

    return Response(message, status=status.HTTP_201_CREATED)
    

#@swagger_auto_schema(method='post',request_body=UserLoginSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    # Проверка входных данных
    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        print(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Аутентификация пользователя
    user = authenticate(request, **serializer.validated_data)
    if user is None:
        message = {"message": "Пользователь не найден"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)

    # Создание токена доступа
    access_token = create_access_token(user.id)

    # Сохранение данных пользователя в кеше
    user_data = {
       "user_id": user.id,
       "user_name": user.username,
       "user_email": user.email,
       "is_superuser": user.is_superuser,
       "access_token": access_token
    }
    access_token_lifetime = settings.ACCESS_TOKEN_LIFETIME
    cache.set(access_token, user_data, access_token_lifetime)

    # Отправка ответа с данными пользователя и установкой куки
    response_data = {
        "user_id": user.id,
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
@api_view(['GET'])
@permission_classes([AllowAny])
#@swagger_auto_schema(method='GET')
def get_plants(request, format=None):
    plant_name_r = request.GET.get('plant_name')
    collectionID = 0
    token = get_access_token(request)
    if token != 'undefined':
        payload = get_jwt_payload(token)
        user_id = payload["user_id"]
        curr_user = CustomUser.objects.get(id = user_id)
        print("uuuuuuu", curr_user)

        # try {        #     drug = Medical_drug.objects.get(user_id_id=user_id, status=0)
        if curr_user.is_superuser:
            print("curr_user.is_superuser")
            if plant_name_r:
                plants = Plant.objects.filter(
                    Q(plant_name__icontains = plant_name_r.lower())
                )       
            else:
                plants = Plant.objects.all()
                print(plants)
            try:
                collection = Collection.objects.get(user_id=user_id, status=0)
                collectionID = collection.id
            except Collection.DoesNotExist:
                collectionID = 0
        else:
            try:
                collection = Collection.objects.get(user_id=user_id, status=0)
                collectionID = collection.id
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
    plant = get_object_or_404(Plant, id=id)
    if request.method == 'GET':
        serializer = PlantSerializer(plant)
        return Response(serializer.data)



# добавление нового растения (услуги)
#@swagger_auto_schema(method='post',request_body=PlantSerializer)
@api_view(['POST'])
@permission_classes([IsManager])
def add_new_plant(request, format=None):

    data = request.POST.dict()
    image_file = request.FILES.get('image')

    if image_file:
        image_data = b64encode(image_file.read()).decode('utf-8')
        data['image'] = image_data

    serializer = PlantSerializer(data=data)
    if serializer.is_valid():
        serializer.save()  
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)



# обновление информации о заболевании (услуге)
#@swagger_auto_schema(method='put', request_body=PlantSerializer)
@api_view(['PUT'])
@permission_classes([IsManager])
@authentication_classes([])
def update_plant(request, id, format=None):
    plant = get_object_or_404(Plant, id=id)


    image_file = request.FILES.get('image')
    if image_file:
        # Создание и сохранение изображения в формате base64
        image_data = b64encode(image_file.read()).decode('utf-8')
        plant.image = image_data

    # Обновление других полей растения
    plant.plant_name = request.data.get('plant_name', plant.plant_name)
    plant.plant_class.class_name = request.data.get('plant_class_name', plant.plant_class.class_name)
    plant.general_info = request.data.get('general_info', plant.general_info)
    plant.properties = request.data.get('properties', plant.properties)

    plant.save()
    
    return Response(status=status.HTTP_200_OK)



# удаление информации о заболевании (услуге)
@api_view(['DELETE'])
@permission_classes([IsManager])
@authentication_classes([BasicAuthentication])
def delete_plant(request, id, format=None):
    print('delete', id)
    plant = get_object_or_404(Plant, id=id)
    print(plant.status)
    plant.status="d"
    plant.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


# добавление услуги в заявку
#@swagger_auto_schema(method='post', request_body=PlantSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_plant_to_collection(request, id):
    print("add pl to coll", id)

    if not Plant.objects.filter(id=id).exists():
        return Response(f"Растения с таким id не найдено")
    
    token = get_access_token(request)
    if not token:
        return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)


    payload = get_jwt_payload(token)
    user_id = payload["user_id"]
    print("user", user_id)
    
    plant = Plant.objects.get(id=id)
    collection = Collection.objects.get(status=0, user_id=user_id)

    if collection is None:
        collection = Collection.objects.create()
        collection.user_id = user_id

        recommendation = Recommendation.objects.create()
        recommendation.user_id = user_id

    collection.includes_plants.add(plant)
    collection.save()

    serializer = PlantSerializer(collection.includes_plants, many=True)
    return Response(serializer.data)
    



# список препаратов (заявок)
# @permission_classes([IsAuthenticated])
#@swagger_auto_schema(method='get')
@permission_classes([IsAuthenticated])
@authentication_classes([BasicAuthentication])
@api_view(['GET'])
def get_collections(request, format=None):

    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)

    collection_name_r = request.GET.get('collection_name') ## поиск коллекции по названию
    # time_create= request.GET.get('time_create')
    status_r= request.GET.get('status') ## фильтрация по статусу

    if not curr_user.is_superuser:
        # обычный пользователь может просматривать все коллекции
        collections= Collection.objects.order_by('-time_create').order_by('-status').filter(user_id=user_id)
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
    else:
        return Response("Для админов нет доступа для просмотра коллекций")


# информация о препарате (заявке)
# @permission_classes([IsAuthenticated])
#@swagger_auto_schema(method='get')
@permission_classes([IsAuthenticated])
@authentication_classes([BasicAuthentication])
@api_view(['GET'])
def get_collection(request, id, format=None):
    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)

    collection = get_object_or_404(Collection, id=id)
    serializer = CollectionSerializer(collection)

    if not curr_user.is_superuser:
        if collection:
            if collection.user_id == user_id:
                return Response(serializer.data)
    else:
        return Response("Нет доступа к данным")
            


    # token = get_access_token(request)
    # if not token:
    #     # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
    #     return Response('Нет токена')
    
    # payload = get_jwt_payload(token)
    # user_id = payload["user_id"]

    # try:
    #     drug = Medical_drug.objects.get(id=id)
    # except Medical_drug.DoesNotExist:
    #     return Response('Нет токена')
    
    # if drug.user_id_id==user_id:
   
    #     serializer = DrugSerializer(drug)

    #     return Response(serializer.data)
    # else:
    #     return Response("У данного пользователя нет препарата с таким id")



@api_view(['DELETE'])
@authentication_classes([BasicAuthentication])
def delete_collection(request, id, format=None):

    collection = get_object_or_404(Collection, id=id)
    collection.status = 2
    collection.save()
    return Response(status=status.HTTP_200_OK)
    



# удаление препарата-черновика (заявки)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([BasicAuthentication])
def delete_editing_collection(request, format=None):

    token = get_access_token(request)
    if not token:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if not Collection.objects.filter(status=0).exists():
        return Response(f"Коллекции со статусом 'Черновик' не существует")
    

    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)
    
    
    editing_collection = Collection.objects.get(status=0, user_id=user_id)
    editing_collection.status=2
    editing_collection.save()
    editing_collection.includes_plants.clear()
    serializer = CollectionSerializer(editing_collection, many=False)
    return Response(serializer.data)



# удаление заболевания из связанного с ним препарата (из м-м)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_plant_from_collection(request, collection_id_r, plant_id_r, format=None):
    print('delete_plant_from_collection')

    token = get_access_token(request)
    if not token:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    if not Collection.objects.filter(id=collection_id_r).exists():
        return Response(f"Коллекции с таким id не существует")
    if not Plant.objects.filter(id=plant_id_r).exists():
        return Response(f"Растения с таким id не существует")
    
    
    plant = Plant.objects.get(id=plant_id_r)
    print("plant =", plant)
    collection = Collection.objects.get(id=collection_id_r)
    print("collection =", collection)
    if collection.includes_plants.exists():
        collection.includes_plants.remove(plant)
        collection.save()
        return Response(f"Удаление выбранного растения из коллекции выполнено")
    else:
        return Response(f"Объекта выбранного растения для удаления из коллекции не найдено", status = status.HTTP_404_NOT_FOUND)
    

# @permission_classes([AllowAny])
# @authentication_classes([])
#@swagger_auto_schema(method='put', request_body=CollectionSerializer)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def collection_upd_status_to_created(request, id):
    token = get_access_token(request)
    if not token:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
        
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    if not Collection.objects.filter(id=id).exists():
        return Response(f"Коллекции с таким id не существует")
    
    # Подключение к асинхронному веб-сервису
    
    collection = Collection.objects.get(id=id)
    collection.status=1
    collection.save()
    return Response({'message': 'Успешно обновлен статус коллекции на "Сформирован"'}, status=status.HTTP_200_OK)
    

# @permission_classes([AllowAny])
# @authentication_classes([])
#@swagger_auto_schema(method='put', request_body=CollectionSerializer)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def collection_upd_status_to_editing(request, id):
    token = get_access_token(request)
    if not token:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
        
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    if not Collection.objects.filter(id=id).exists():
        return Response(f"Коллекции с таким id не существует")
    
    # Подключение к асинхронному веб-сервису
    
    collection = Collection.objects.get(id=id)
    collection.status=0
    collection.save()
    return Response({'message': 'Успешно обновлен статус коллекции на "Черновик"'}, status=status.HTTP_200_OK)


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
    





# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


#@swagger_auto_schema(method='get')
@api_view(['GET'])
# @permission_classes([AllowAny])
# @authentication_classes([BasicAuthentication])
def get_users(request,format=None):
    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


# информация о препарате (заявке)
# @permission_classes([IsAuthenticated])
#@swagger_auto_schema(method='get')
@permission_classes([IsAuthenticated])
@authentication_classes([BasicAuthentication])
@api_view(['GET'])
def get_recommendation(request, id_rec, format=None):
    token = get_access_token(request)
    if not token:
        # return Response({"error": "Access token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response('Нет токена')
    
    payload = get_jwt_payload(token)
    user_id = payload["user_id"]

    curr_user = CustomUser.objects.get(id = user_id)
    print("cccccccccccurrr uuser =", curr_user)

    recommendation = get_object_or_404(Recommendation, id=id_rec)
    serializer = RecommendationSerializer(recommendation)

    if not curr_user.is_superuser:
        if recommendation:
            # Здесь вставить алгоритм для построения рекомендаций
            # на основе карточек растений в collection.includes_plants
            # Например, если у вас есть список всех растений в коллекции:
            # collection = Collection.objects.get(user_id=user_id, recomendation = id_rec)
            # recommended_plants = algorithm_to_get_recommendations(collection.includes_plants.all())

                    # Здесь добавляем растения с id = 1 и 2 пока по умолчанию, потом добавим мл по рекомендашкам сюда
            default_plants = Plant.objects.filter(id__in=[1, 2])
            for plant in default_plants:
                recommendation.includes_plants.add(plant)  # Добавляем растения в рекомендацию
            serializer = RecommendationSerializer(recommendation)
            return Response(serializer.data)
        else:
            return Response("Нет данных по коллекции для формирования рекомендаций")
    else:
        return Response("Нет доступа к данным")
            

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
    
