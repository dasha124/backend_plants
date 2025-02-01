# поля, которые вы хотели бы, чтобы преобразовывались в JSON и отправлялись клиенту.
# Сериализаторы были придуманы для того, чтобы преобразовывать наши модели из базы данных в JSON и наоборот.
from backend_plants.models import *
from rest_framework import serializers
from collections import OrderedDict

# ------------------------------------------------------------------------------------------------

# растение 
class PlantClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Class
        fields = ['class_name']

class GetPlantClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Class
        fields = '__all__'


# ------------------------------------------------------------------------------------------------

class PlantSubclassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Subclass
        fields = ['subclass_name']


class GetPlantSubclassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Subclass
        fields = '__all__'

# ------------------------------------------------------------------------------------------------

class PlantTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Type
        fields = ['type_name']

class GetPlantTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant_Type
        fields = '__all__'


# ------------------------------------------------------------------------------------------------
class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__' 


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__'


# ------------------------------------------------------------------------------------------------

class PlantSerializer(serializers.ModelSerializer):
    plant_class = PlantClassSerializer()
    plant_subclass = PlantSubclassSerializer()
    plant_type = PlantTypeSerializer()

    class Meta:
        model = Plant
        fields= ["plant_id", "plant_name", "plant_class", "plant_subclass", "plant_type", "image_url_plant", "general_info", "properties"]

    def get_plant_id(self, obj):
        return obj.plant_id
    def get_plant_name(self, obj):
        return obj.plant_name
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['plant_class'] = representation['plant_class']['class_name']  # Convert plant_class
        if representation['plant_subclass']:
            representation['plant_subclass'] = representation['plant_subclass']['subclass_name']  # Convert plant_subclass
        representation['plant_type'] = representation['plant_type']['type_name']  # Convert plant_type
        return representation
    # def get_plant_class(self, obj):
    #     return obj.plant_class.class_name if obj.plant_class else None
    
    # def get_plant_subclass(self, obj):
    #     return obj.plant_subclass.subclass_name if obj.plant_subclass else None
    
    def create(self, validated_data):
        plant_class_name = validated_data.pop('plant_class')
        plant_subclass_name = validated_data.pop('plant_subclass', None)

        # Получаем или создаем Plant_Class
        plant_class, created = Plant_Class.objects.get_or_create(class_name=plant_class_name)

        # Получаем или создаем Plant_Subclass, если оно предоставлено
        plant_subclass = None
        if plant_subclass_name:
            plant_subclass, _ = Plant_Subclass.objects.get_or_create(subclass_name=plant_subclass_name, plant_class=plant_class)

        plant = Plant.objects.create(
            plant_class=plant_class,
            plant_subclass=plant_subclass,
            **validated_data
        )
        return plant

    def with_collection(self, instance):
       representation = super().to_representation(instance)
       representation['collectionID'] = 0 # добавляем collectionID в сериализованные данные
       return representation

# ------------------------------------------------------------------------------------------------
class GetPlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields= ["plant_id", "plant_name", "plant_class", "plant_subclass", "plant_type", "image_url_plant", "general_info", "properties"]

    def get_plant_id(self, obj):
        return obj.plant_id
    def get_plant_name(self, obj):
        return obj.plant_name
    # def get_plant_class(self, obj):
    #     return obj.plant_class.class_name if obj.plant_class else None
    
    # def get_plant_subclass(self, obj):
    #     return obj.plant_subclass.subclass_name if obj.plant_subclass else None
    
    def create(self, validated_data):
        plant_class_name = validated_data.pop('plant_class')
        plant_subclass_name = validated_data.pop('plant_subclass', None)

        # Получаем или создаем Plant_Class
        plant_class, created = Plant_Class.objects.get_or_create(class_name=plant_class_name)

        # Получаем или создаем Plant_Subclass, если оно предоставлено
        plant_subclass = None
        if plant_subclass_name:
            plant_subclass, _ = Plant_Subclass.objects.get_or_create(subclass_name=plant_subclass_name, plant_class=plant_class)

        plant = Plant.objects.create(
            plant_class=plant_class,
            plant_subclass=plant_subclass,
            **validated_data
        )
        return plant

    def with_collection(self, instance):
       representation = super().to_representation(instance)
       representation['collectionID'] = 0 # добавляем collectionID в сериализованные данные
       return representation


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields= "__all__"


class CollectionsSerializer(serializers.ModelSerializer):

    plant = PlantSerializer(read_only = True, many=True, source='includes_plants')
    user_id = serializers.CharField(source='user.username', read_only=True)

    
    class Meta:
        model = Collection
        exclude = ['includes_plants']

class CollectionPlantSerializer(serializers.ModelSerializer):
    collection_name = serializers.CharField(source='collection.collection_name', read_only=True)
    plant = PlantSerializer(read_only=True)

    class Meta:
        model = CollectionPlant
        fields = ['collection_plant_id', 'collection_name', 'plant', 'date_add', 'time_add']

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


class AdminRegisterSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    class Meta:
        model = AdminUser
        fields = ('admin_id', 'email', 'password', 'is_staff', 'is_superuser', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('admin_id',)

    def create(self, validated_data):
        is_staff = validated_data.pop('is_staff', True)
        is_superuser = validated_data.pop('is_superuser', True)

        admin = AdminUser.objects.create(
            email=validated_data['email'],
            username = validated_data['username']
        )

        admin.set_password(validated_data['password'])

        admin.is_staff = is_staff
        admin.is_superuser = is_superuser

        admin.save()

        return admin


class UserRegisterSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    class Meta:
        model = CustomUser
        fields = ('user_id', 'email', 'password', 'is_staff', 'is_superuser', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('user_id',)

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
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['user_id', 'email', 'username', 'is_superuser']

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ['admin_id', 'email', 'is_superuser']

        # def get_fields(self):
        #     new_fields = OrderedDict()
        #     for name, field in super().get_fields().items():
        #         field.required = False
        #         new_fields[name] = field
        #     print("NF =", new_fields)
        #     return new_fields
