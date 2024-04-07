from django.urls import path, include
from . import views

urlpatterns = [
    path('startup', views.startup),
    path('register', views.register),
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout),
    path('boards', views.boards),
    path('user', views.delete_account),
    path('boards/<index>', views.boards_index),
    path('user/<username>', views.user_board),
    
    path('friends/delete', views.delete_friend),
    path('friends/label', views.label_friend),
    path('friends/list', views.list_friend),
    path('friend/send_friend_request', views.send_friend_request),
    path('friend/respond_friend_request', views.respond_friend_request),
    path('friend/friend_request_list', views.list_friend_request),
    
    path('modify', views.modify_profile)
]
