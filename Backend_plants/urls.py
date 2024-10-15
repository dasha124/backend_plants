

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

   # для растений (=услуг)
   path(r'api/plants/', views.get_plants, name='get_plants'), # (get)
   path(r'api/plants/<int:id>/', views.get_plant, name='get_plant'), # (get)
   path(r'api/plants/add_plant/', views.add_new_plant, name='add_new_plant'), # (post) раньше назыв /disease/post/
   path(r'api/plants/<int:id>/update_plant/', views.update_plant, name='update_plant'), # (put)
   path(r'api/plants/<int:id>/delete_plant/', views.delete_plant, name='delete_plant'), # (del)
   path(r'api/plants/<int:id_plant>/<int:id_collection>/add_plant_to_collection/', views.add_plant_to_collection, name='add_plant_to_collection'), # (post)


   # для избранных коллекций растений (=заявок)
   path(r'api/collections/', views.get_collections, name='get_collections'),
   path(r'api/collections/<int:id>/', views.get_collection, name='get_collection'),
   path(r'api/collections/<int:id>/delete/', views.delete_collection,name='delete_collection'),
   path(r'api/collections/delete_editing_collection/', views.delete_editing_collection,name='delete_editing_collection'),
   path(r'api/collections/<int:id_collection>/<int:id_plant>/delete_plant_from_collection/', views.delete_plant_from_collection, name='delete_plant_from_colln'),
   path(r'api/collections/<int:id>/update_st_user/', views.collection_upd_status_to_created,name='collection_update_status_user'), #put - сформировать заявку=коллекцию
   path(r'api/collections/<int:id>/update_st_user/', views.collection_upd_status_to_editing,name='collection_upd_status_to_editing'), #put - статус заявки=черновик
   #path(r'api/collections/<int:id>/edit/', views.edit_collection,name='edit_collection'), #put - заявки=черновик/ поменять статус и сразу открыть в окне для корзины
   path(r'api/get_users/', views.get_users, name='get_users'),

   # для рекомендаций растений (=заявок)
   # path(r'api/recommendations/', views.get_recommendations, name='get_recommendations'),  -  это не надо смотреть юзикам, по сути этого нет, просто список idшек
   path(r'api/recommendarions/<int:id>/', views.get_recommendation, name='get_recommendation'),
   # path(r'api/get_users/', views.get_users, name='get_users'),

   path(r'api/register/', views.register, name="register"),
   path(r'api/login/',  views.login_view, name='login'),
   path(r'api/logout/', views.logout_view, name='logout'),
   path(r'api/check/', views.check, name='check'),



   # path(r'api/async_result/', views.async_result),

   # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),


]
