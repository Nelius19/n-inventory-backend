from django.urls import path
from . import views

# 
urlpatterns = [
    path('scan/', views.scan_item),
    path('item/', views.create_item),
    path('item/<int:house_id>/', views.destock_item),
    path('items/<int:house_id>/', views.fetch_items),
    path('edit/<int:item_id>/', views.edit_item),
    path('delete/<int:item_id>/', views.delete_item),
    path('category/', views.create_category),
    path('categories/', views.fetch_categories),
    path('category/edit/<int:category_id>/<int:house_id>/', views.edit_category),
    path('category/delete/<int:category_id>/<int:house_id>/', views.delete_category),

    path('history/<int:house_id>/', views.fetch_item_history),
]
