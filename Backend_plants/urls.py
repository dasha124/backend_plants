from django.contrib import admin
from django.urls import path, include
from backend_plants import views
from rest_framework import routers
from rest_framework import permissions
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from recs.search_plant import *
from recs.imgs_from_minio import *

router = routers.DefaultRouter()

urlpatterns = [
   path('', include(router.urls)),
   path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
   path('admin/', admin.site.urls),


   # для растений
   path(r'api/plants/classes/', views.get_plant_classes, name='get_plant_classes'), # (get)
   path(r'api/plants/subclasses/', views.get_plant_subclasses, name='get_plant_subclasses'), # (get)
   path(r'api/plants/types/', views.get_plant_types, name='get_plant_types'), # (get)
   path(r'api/plants/', views.get_plants, name='get_plants'), # (get)
   path(r'api/plants/<int:id>/', views.get_plant, name='get_plant'), # (get)
   path(r'api/plants/add_plant/', views.add_new_plant, name='add_new_plant'), # (post)
   path(r'api/plants/<int:id>/update_plant/', views.update_plant, name='update_plant'), # (put)
   path(r'api/plants/<int:id>/delete_plant/', views.delete_plant, name='delete_plant'), # (del)
   # path(r'api/plants/<int:id>/obj_delete_plant/', views.obj_delete_plant, name='obj_delete_plant'), # (del)

   # для избранных коллекций растений
   path(r'api/collections/', views.get_collections, name='get_collections'),
   path(r'api/collections/<int:id>/', views.get_collection, name='get_collection'),
   path(r'api/collections/create/', views.create_collection, name='create_collection'),
   path(r'api/collections/<int:id>/update/', views.update_collection, name='update_collection'),
   path(r'api/collections/<int:id>/delete/', views.delete_collection,name='delete_collection'),
   path(r'api/collections/<int:id_plant>/<int:id_coll>/add_plant_to_collection/', views.add_plant_to_collection, name='add_plant_to_collection'), # (post)
   path(r'api/collections/<int:id_collection>/<int:id_plant>/delete_plant_from_collection/', views.delete_plant_from_collection, name='delete_plant_from_colln'),
   
   path(r'api/plant/search', predictImage, name='search_plant'),
   path(r'api/recommendations/coll/<int:id_coll>/', views.get_recommendation_by_coll, name='get_recommendation_by_coll'),
   path(r'api/recommendations/plant/<int:id_plant>/', views.get_recommendation_by_plant, name='get_recommendation_by_plant'),
   path(r'api/recommendarions/Expert/', views.get_recommendation_by_Expert, name='get_recommendation'),

   path(r'api/from_minio/', views.get_image_sizes_from_minio, name='get_image_sizes_from_minio'),

   path(r'api/register/', views.register, name="register"),
   path(r'api/register_admin/', views.register_admin, name="register_admin"),
   path(r'api/login/',  views.login_view, name='login'),
   path(r'api/logout/', views.logout_view, name='logout'),
   path(r'api/check/', views.check, name='check'),
   path(r'api/get_user/<int:id>/', views.get_user, name='get_users'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
