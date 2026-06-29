from django.urls import path
from . import views

# 
urlpatterns = [
    path('csrf/', views.get_csrf),
    path('register/', views.register_user),
    path('login/', views.login_user),
    path('me/', views.user_session),
    path('logout/', views.logout_user),
    path('password-reset/', views.password_reset_request),
    path('set-new-password/', views.set_new_password),

    path('data/update/', views.update_user),
    path('password/update/', views.update_password),
]
