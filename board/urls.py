from django.urls import path, include
from . import views

urlpatterns = [
    path('startup', views.startup),
    path('register', views.register),
    path('login', views.login, name='login'),
    path('logout', views.logout),
    path('boards', views.boards),
    path('user', views.delete_account),
    path('boards/<index>', views.boards_index),
    path('user/<username>', views.user_board),
    path('friends/delete', views.delete_friend)
]
