

from django.contrib import admin
from django.urls import path, include
from backend_plants import views
from rest_framework import routers
from rest_framework import permissions
from django.urls import path, include
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

router = routers.DefaultRouter()



# schema_view = get_schema_view(
#    openapi.Info(
#       title="Snippets API",
#       default_version='v1',
#       description="Test description",
#       terms_of_service="https://www.google.com/policies/terms/",
#       contact=openapi.Contact(email="contact@snippets.local"),
#       license=openapi.License(name="BSD License"),
#    ),
#    public=True,
#    permission_classes=(permissions.AllowAny,),
# )


urlpatterns = [
   path('', include(router.urls)),
   path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
   path('admin/', admin.site.urls),


   # для растений
   path(r'api/plants/classes/', views.get_plant_classes, name='get_plant_classes'), # (get)
   path(r'api/plants/subclasses/', views.get_plant_subclasses, name='get_plant_subclasses'), # (get)
   path(r'api/plants_0/', views.get_plants_0, name='get_plants_0'), # (get)
   path(r'api/plants/', views.get_plants, name='get_plants'), # (get)
   path(r'api/plants/<int:id>/', views.get_plant, name='get_plant'), # (get)
   path(r'api/plants/add_plant/', views.add_new_plant, name='add_new_plant'), # (post) раньше назыв /disease/post/
   path(r'api/plants/<int:id>/update_plant/', views.update_plant, name='update_plant'), # (put)
   path(r'api/plants/<int:id>/delete_plant/', views.delete_plant, name='delete_plant'), # (del)
   path(r'api/plants/<int:id>/obj_delete_plant/', views.obj_delete_plant, name='obj_delete_plant'), # (del)
   path(r'api/plants/<int:id>/add_plant_to_collection/', views.add_plant_to_collection, name='add_plant_to_collection'), # (post)


   # для избранных коллекций растений
   path(r'api/collections/', views.get_collections, name='get_collections'), #активные, без черновиков
   path(r'api/collections/get_entered/', views.get_entered_collection, name='get_entered_collection'),
   path(r'api/collections/deleted_collections/', views.get_deleted_collections, name='get_deleted_collections'),
   path(r'api/collections/<int:id>/', views.get_collection, name='get_collection'),
   path(r'api/collections/<int:id>/update/', views.update_collection, name='update_collection'),
   path(r'api/collections/<int:id>/delete/', views.delete_collection,name='delete_collection'), # логическое удаление
   path(r'api/collections/<int:id>/obj_delete/', views.delete_obj_collection,name='delete_obj_collection'), # физическое удаление
   path(r'api/collections/delete_editing_collection/', views.delete_editing_collection,name='delete_editing_collection'),
   path(r'api/collections/<int:id_collection>/<int:id_plant>/delete_plant_from_collection/', views.delete_plant_from_collection, name='delete_plant_from_colln'),
   path(r'api/collections/update_st_user_to_create/', views.collection_upd_status_to_created,name='collection_update_status_user'), #put - сформировать заявку=коллекцию
   path(r'api/collections/<int:id>/update_st_user_to_edit/', views.collection_upd_status_to_editing,name='collection_upd_status_to_editing'), #put - статус заявки=черновик
   #path(r'api/collections/<int:id>/edit/', views.edit_collection,name='edit_collection'), #put - заявки=черновик/ поменять статус и сразу открыть в окне для корзины
   path(r'api/collections/<int:id>/update_st_user_to_create_from_del/', views.collection_upd_status_to_created_from_del,name='collection_upd_status_to_created_from_del'), #put - сформировать заявку=коллекцию
   
   
   # получение списка юзиков
   path(r'api/get_users/', views.get_users, name='get_users'),
   path(r'api/get_admins/', views.get_admins, name='get_admins'),
   path(r'api/users/<int:id>/delete/', views.obj_delete_user, name='obj_delete_user'), # (del)


   # для рекомендаций растений (=заявок)
   # path(r'api/recommendations/', views.get_recommendations, name='get_recommendations'),  -  это не надо смотреть юзикам, по сути этого нет, просто список idшек
   


   
   # #TODO - если прикручивать получение рекомендации просто по карточке растения - надо делать без id
   # path(r'api/recommendarions/<int:id>/', views.view_recommendation, name='get_recommendation'), # get = view
   # # +
   path(r'api/recommendarions/coll/<int:id_collection>/', views.get_recommendation_by_coll, name='get_recommendation_by_coll'),
   path(r'api/recommendarions/plant/<int:id_plant>/', views.get_recommendation_by_plant, name='get_recommendation_by_plant'),
   # path(r'api/recommendarions/LLM/', views.get_recommendation_by_LLM, name='get_recommendation'),
   # path(r'api/recommendarions/Expert/', views.get_recommendation_by_Expert, name='get_recommendation'),
   # path(r'api/recommendarions/<int:id>/delete', views.del_recommendation, name='del_recommendation'),
   # # path(r'api/get_users/', views.get_users, name='get_users'),


   # получение размеров картинки через минио
   path(r'api/from_minio/', views.get_image_sizes_from_minio, name='get_image_sizes_from_minio'),



   path(r'api/register/', views.register, name="register"),
   path(r'api/register_admin/', views.register_admin, name="register_admin"),
   path(r'api/login/',  views.login_view, name='login'),
   path(r'api/logout/', views.logout_view, name='logout'),
   path(r'api/check/', views.check, name='check'),





   # path(r'api/async_result/', views.async_result),

   # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),


]
