from django.urls import path
from . import views

# 
urlpatterns = [
    path('data/', views.getMemberShip),
    path('members/<int:house_id>/', views.house_members),
    path('member/<int:member_id>/<int:house_id>/', views.remove_member),
    path('create/', views.create_house),
    path('edit/', views.edit_house),
    path('delete/<int:house_id>/', views.delete_house),
    path('join/', views.join_house),
    path('leave/<int:house_id>/', views.leave_house),
]
