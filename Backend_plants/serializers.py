# поля, которые вы хотели бы, чтобы преобразовывались в JSON и отправлялись клиенту.
# Сериализаторы были придуманы для того, чтобы преобразовывать наши модели из базы данных в JSON и наоборот.
from models import *
from rest_framework import serializers
from collections import OrderedDict


# растение = услуга
class PlantClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Class
        fields = ['class_name']


class PlantSerializer(serializers.ModelSerializer):
    plant_class_name = serializers.SerializerMethodField()

    class Meta:
        model = Plant
        fields= ["id", "plant_name", "plant_class_name", "image", "general_info", "properties", "moderator_id"]

    def get_plant_class_name(self, obj):
        return obj.plant_class.class_name if obj.plant_class else None
        
    
    def with_collection(self, instance):
       representation = super().to_representation(instance)
       representation['collectionID'] = 0 # добавляем collectionID в сериализованные данные
       return representation


class CollectionSerializer(serializers.ModelSerializer):

    plant = PlantSerializer(read_only = True, many=True, source='includes_plants')
    user_id = serializers.CharField(source='user.username', read_only=True)
    moderator = serializers.CharField(source='user_id.username', read_only=True)

    
    class Meta:
        model = Collection
        fields= "__all__"


class CollectionsSerializer(serializers.ModelSerializer):

    plant = PlantSerializer(read_only = True, many=True, source='includes_plants')
    user_id = serializers.CharField(source='user.username', read_only=True)
    moderator = serializers.CharField(source='moderator.username', read_only=True)

    
    class Meta:
        model = Collection
        exclude = ['includes_plants']


class RecommendationSerializer(serializers.ModelSerializer):

    plant = PlantSerializer(read_only = True, many=True, source='includes_plants')
    
    class Meta:
        model = Recommendation
        fields= "__all__"


class RecommendationsSerializer(serializers.ModelSerializer):

    plant = PlantSerializer(read_only = True, many=True, source='includes_plants')
    
    class Meta:
        model = Recommendation
        exclude = ['includes_plants']


# class DrugSerializer_get(serializers.ModelSerializer):
#     diseases = DiseaseSerializer(read_only = True, many=True) # type: ignore
    
#     class Meta:
#         model = Medical_drug
#         fields= ['id', 'time_create', 'time_form', 'time_finish', 'user_id', 'status', 'diseases']


class UserRegisterSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'password', 'is_staff', 'is_superuser', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        is_staff = validated_data.pop('is_staff', False)
        is_superuser = validated_data.pop('is_superuser', False)

        user = CustomUser.objects.create(
            email=validated_data['email'],
            username = validated_data['username']
        )

        user.set_password(validated_data['password'])

        user.is_staff = is_staff
        user.is_superuser = is_superuser

        user.save()

        return user
    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'is_superuser']

        # def get_fields(self):
        #     new_fields = OrderedDict()
        #     for name, field in super().get_fields().items():
        #         field.required = False
        #         new_fields[name] = field
        #     print("NF =", new_fields)
        #     return new_fields
