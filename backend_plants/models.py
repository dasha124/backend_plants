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
    email = models.EmailField(("email адрес"), unique=True)
    username = models.CharField(max_length=30, default='', verbose_name="Имя пользователя")
    password = models.TextField(max_length=256, verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")

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
    
#----------------------------------------------------------------------------------------------------------------

class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user_name

    class Meta:
        managed = True
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


#----------------------------------------------------------------------------------------------------------------

class Plant_Class(models.Model):
    id = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=100)

    def __str__(self):
        return self.class_name

    class Meta:
        managed = True
        verbose_name = 'Класс растения'
        verbose_name_plural = 'Классы растений'


#----------------------------------------------------------------------------------------------------------------

class Plant(models.Model):
    id = models.AutoField(primary_key=True)
    plant_name = models.CharField(default='Название растения', max_length=150)
    plant_class = models.ForeignKey(Plant_Class, on_delete=models.CASCADE)
    image = models.TextField(default='')
    general_info = models.CharField(default='Описание растения', max_length=255)
    properties = models.JSONField()
    moderator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='moderator', blank=True, null=True)
    STATUSES = [
        ('a', 'active'),
        ('d', 'delited')
    ]
    status = models.CharField(max_length=1, choices=STATUSES, default='a')



    def __str__(self):
        # print("return self.name")
        return self.plant_name

    def class_name(self):
        return self.plant_class.class_name
    
    def image64(self):
        # print("1")
        a= str(self.image.tobytes())[2:]
        a = a[:-1]
        return a
    
    class Meta:
        managed = True
        verbose_name = 'Растение'
        verbose_name_plural = 'Растения'



#----------------------------------------------------------------------------------------------------------------

class Recommendation(models.Model):
    id = models.AutoField(primary_key=True)
    includes_plants = models.ManyToManyField(Plant, through='RecommendationPlant', null=False)

    def plant_names(self):
        return self.includes_plants.all()


    class Meta:
        managed = True
        verbose_name = 'Рекомендация'
        verbose_name_plural = 'Рекомендации'


#----------------------------------------------------------------------------------------------------------------

class Collection(models.Model):
    id = models.AutoField(primary_key=True)
    collection_name = models.CharField(default='Название растения', max_length=150)
    image = models.TextField(default='')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, blank=True, null=True)
    includes_plants = models.ManyToManyField(Plant, through='CollectionPlant', null=False)
    time_create = models.DateField(auto_now_add=True)
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
        managed = True
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'


#----------------------------------------------------------------------------------------------------------------

class CollectionPlant(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.collection}   -   {self.plant}"


    class Meta:
        managed = True
        verbose_name = 'КоллекцияРастение'
        verbose_name_plural = 'КоллекцииРастения'



#----------------------------------------------------------------------------------------------------------------

class RecommendationPlant(models.Model):
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.recommendation}   -   {self.plant}"
    

    class Meta:
        managed = True
        verbose_name = 'РекомендацияРастение'
        verbose_name_plural = 'РекомендацииРастения'






   
