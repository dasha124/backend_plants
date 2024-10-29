from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager, UserManager
from django.contrib.auth.models import Group, Permission

#----------------------------------------------------------------------------------------------------------------

class NewUserManager(BaseUserManager):

    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('Поле "email" обязательно')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    

#----------------------------------------------------------------------------------------------------------------

class CustomUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    email = models.EmailField(("email адрес"), unique=True)
    username = models.CharField(max_length=30, default='', verbose_name="Имя пользователя")
    password = models.TextField(max_length=256, verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь суперюзером?")

    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, verbose_name=("groups"), blank=True, related_name="custom_user_groups")
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name="custom_user_permissions")

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    objects =  NewUserManager()
    class Meta:
        managed = True
        db_table = 'CustomUser'
    

#----------------------------------------------------------------------------------------------------------------
class AdminUser(CustomUser):
    admin_id = models.AutoField(primary_key=True, db_column='admin_id')

    class Meta:
        db_table = 'AdminUser'
        managed = True
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'


# class AdminUser(AbstractBaseUser, PermissionsMixin):
#     admin_id = models.AutoField(primary_key=True, db_column='admin_id')
#     email = models.EmailField(("email адрес"), unique=True)
#     username = models.CharField(max_length=30, default='', verbose_name="Имя пользователя")
#     password = models.TextField(max_length=256, verbose_name="Пароль")    
#     is_staff = models.BooleanField(default=True, verbose_name="Является ли пользователь менеджером?")
#     is_superuser = models.BooleanField(default=True, verbose_name="Является ли пользователь суперюзером?")

#     is_active = models.BooleanField(default=True)
#     groups = models.ManyToManyField(Group, verbose_name=("groups"), blank=True, related_name="admin_user_groups")
#     user_permissions = models.ManyToManyField(Permission, blank=True, related_name="admin_user_permissions")

#     USERNAME_FIELD = 'email'
#     # REQUIRED_FIELDS = ['username']
#     objects =  NewUserManager()
#     class Meta:
#         db_table = 'AdminUser'
#         managed = True
#         verbose_name = 'Администратор'
#         verbose_name_plural = 'Администраторы'


#----------------------------------------------------------------------------------------------------------------

class User(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    user_name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user_name

    class Meta:
        db_table = 'User'
        managed = True
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


#----------------------------------------------------------------------------------------------------------------

class Plant_Class(models.Model):
    plant_class_id = models.AutoField(primary_key=True, db_column='plant_class_id')
    class_name = models.CharField(max_length=100, verbose_name='Название класса растения')

    def __str__(self):
        return self.class_name

    class Meta:
        db_table = 'Plant_Class'
        managed = True
        verbose_name = 'Класс растения'
        verbose_name_plural = 'Классы растений'


#----------------------------------------------------------------------------------------------------------------
class Plant_Subclass(models.Model):
    plant_subclass_id = models.AutoField(primary_key=True, db_column='plant_subclass_id')
    subclass_name = models.CharField(max_length=100, verbose_name='Название подкласса растения')
    plant_class = models.ForeignKey(Plant_Class, verbose_name='Название класса растения', related_name='subclasses', on_delete=models.CASCADE, db_column='plant_class_id')

    def __str__(self):
        return self.subclass_name

    class Meta:
        db_table = 'Plant_Subclass'
        managed = True
        verbose_name = 'Подкласс растения'
        verbose_name_plural = 'Подклассы растений'


#----------------------------------------------------------------------------------------------------------------

class Plant(models.Model):
    plant_id = models.AutoField(primary_key=True, db_column='plant_id')
    plant_name = models.CharField(verbose_name='Название растения', max_length=150)
    plant_class = models.ForeignKey(Plant_Class, verbose_name='Название класса растения', on_delete=models.CASCADE, db_column='plant_class_id')
    plant_subclass = models.ForeignKey(Plant_Subclass, verbose_name='Название подкласса растения', null=True, blank=True, on_delete=models.SET_NULL,  db_column='plant_subclass_id')
    image_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='Фото растения')
    general_info = models.CharField(verbose_name='Описание растения', max_length=255)
    properties = models.JSONField(verbose_name='Характеристики растения')
    STATUSES = [
        ('a', 'active'),
        ('d', 'delited')
    ]
    status = models.CharField(max_length=1, choices=STATUSES, default='a', verbose_name='Статус растения')

    def __str__(self):
        # print("return self.name")
        return self.plant_name

    def class_name(self):
        return self.plant_class.class_name
    
    def subclass_name(self):
        return self.plant_subclass.subclass_name
    
    def image64(self):
        # print("1")
        a= str(self.image.tobytes())[2:]
        a = a[:-1]
        return a
    
    class Meta:
        db_table = 'Plant'
        managed = True
        verbose_name = 'Растение'
        verbose_name_plural = 'Растения'



#----------------------------------------------------------------------------------------------------------------

class Recommendation(models.Model):
    recommendation_id = models.AutoField(primary_key=True, db_column='recommendation_id')
    includes_plants = models.ManyToManyField(Plant, through='RecommendationPlant', null=False)
    last_modified_date = models.DateField(auto_now=True, verbose_name='Дата последнего изменения рекомендации')
    last_modified_time = models.TimeField(auto_now=True, verbose_name='Время последнего изменения рекомендации')

    def plant_names(self):
        return self.includes_plants.all()


    class Meta:
        db_table = 'Recommendation'
        managed = True
        verbose_name = 'Рекомендация'
        verbose_name_plural = 'Рекомендации'


#----------------------------------------------------------------------------------------------------------------

class Collection(models.Model):
    collection_id = models.AutoField(primary_key=True, db_column='collection_id')
    collection_name = models.CharField(verbose_name='Название коллекции', max_length=150)
    image_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='Фото коллекции')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1, verbose_name='Создатель', db_column='user_id')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, blank=True, null=True,  db_column='recommendation_id')
    includes_plants = models.ManyToManyField(Plant, through='CollectionPlant', null=False)
    date_create = models.DateField(auto_now_add=True, verbose_name='Дата создания коллекции')
    time_create = models.TimeField(auto_now_add=True, verbose_name='Время создания коллекции')
    STATUSES = [
        (0, 'Черновик'), # Черновик - 'entered'
        (1, 'Сформирован'), # на рассмотрениии - 'in operation'  - юзер смена
        (2, 'Удалён') # удалён - 'deleted'  - юзер смена
    ]
    status = models.IntegerField(choices=STATUSES, default=0)


    def __str__(self):
        # print("return self.name")
        return self.collection_name
    
    def plant_names(self):
        return self.includes_plants.all()
    
    def get_coll_display_word(self):
        collection_status = dict(self.STATUSES)
        return collection_status.get(self.status, 'Неизвестный статус')

    
    def image64(self):
        # print("1")
        a= str(self.image.tobytes())[2:]
        a = a[:-1]
        return a
    
    class Meta:
        db_table = 'Collection'
        managed = True
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'


#----------------------------------------------------------------------------------------------------------------

class CollectionPlant(models.Model):
    collection_plant_id = models.AutoField(primary_key=True, db_column='collection_plant_id')
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, verbose_name='Коллекция', db_column='collection_id')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, verbose_name='Растение', db_column='plant_id')
    date_add = models.DateField(auto_now=True, verbose_name='Дата обновления растений в коллекции')
    time_add = models.TimeField(auto_now=True, verbose_name='Время обновления растений в коллекции')


    def __str__(self):
        return f"{self.collection}   -   {self.plant}"


    class Meta:
        db_table = 'CollectionPlant'
        managed = True
        verbose_name = 'КоллекцияРастение'
        # verbose_name_plural = 'КоллекцииРастения'



#----------------------------------------------------------------------------------------------------------------

class RecommendationPlant(models.Model):
    recommendation_plant_id = models.AutoField(primary_key=True, db_column='recommendation_plant_id')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, verbose_name="Рекомендация", db_column='recommendation_id')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, verbose_name='Растение', db_column='plant_id')
    weight = models.IntegerField(default=5, verbose_name='Вес растения в рекомендации')


    def __str__(self):
        return f"{self.recommendation}   -   {self.plant}_(Index_{self.weight})"
    

    class Meta:
        db_table = 'RecommendationPlant'
        managed = True
        verbose_name = 'РекомендацияРастение'
        # verbose_name_plural = 'РекомендацииРастения'


#----------------------------------------------------------------------------------------------------------------

class Action(models.Model):
    action_id = models.AutoField(primary_key=True, db_column='action_id')
    action_name = models.CharField(verbose_name='Название действия', max_length=50)

    # 1 - добавление
    # 2 - изменение
    # 3 - удаление

    def __str__(self):
        return self.action_name
    
    class Meta:
        db_table = 'Action'
        managed = True
        verbose_name = 'Действие'
        verbose_name_plural = 'Действия'

#----------------------------------------------------------------------------------------------------------------

class Interaction(models.Model):
    interaction_id = models.AutoField(primary_key=True, db_column='interaction_id')
    admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='moderator_id', default=1, db_column='user_id')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, verbose_name='Растение', db_column='plant_id')
    action = models.ForeignKey(Action, on_delete=models.CASCADE, db_column='action_id')
    date = models.DateField(auto_now_add=True, verbose_name='Дата взаимодействия админа с растением') # время, когда действие было сделано
    time = models.TimeField(auto_now_add=True, verbose_name='Время взаимодействия админа с растением')

    def __str__(self):
        return f"{self.admin} - {self.plant} - {self.action}"
    
    def action_name(self):
        return self.action.action_name
    
    def plant_name(self):
        return self.plant.plant_name
    
    class Meta:
        db_table = 'Interaction'
        managed = True
        verbose_name = 'Взаимодействие'
        verbose_name_plural = 'Взаимодействия'




   
