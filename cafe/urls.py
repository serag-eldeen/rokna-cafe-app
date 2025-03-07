# cafe/urls.py
from django.urls import path
from . import views

app_name = 'cafe'
urlpatterns = [
    path('', views.home, name='home'),  # Root URL goes to home
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('reserve_table/', views.reserve_table, name='reserve_table'),
    path('reserve_ps_room/', views.reserve_ps_room, name='reserve_ps_room'),
    path('place_order/', views.place_order, name='place_order'),
    path('admin/', views.admin_page, name='admin_page'),
    path('admin/add_table/', views.add_table, name='add_table'),
    path('admin/edit_table/<int:table_id>/', views.edit_table, name='edit_table'),
    path('admin/delete_table/<int:table_id>/', views.delete_table, name='delete_table'),
    path('admin/add_room/', views.add_room, name='add_room'),
    path('admin/edit_room/<int:room_id>/', views.edit_room, name='edit_room'),
    path('admin/delete_room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('admin/add_item/', views.add_item, name='add_item'),
    path('admin/edit_item/<int:item_id>/', views.edit_item, name='edit_item'),
    path('admin/delete_item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
]