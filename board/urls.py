from django.urls import path, include
from . import views

urlpatterns = [
    path('register', views.register),
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout),
    path('delete_user', views.delete_account),
    path('friends/delete', views.delete_friend),
    path('friends/label', views.label_friend),
    path('friends/list', views.list_friend),
    path('friend/send_friend_request', views.send_friend_request),
    path('friend/respond_friend_request', views.respond_friend_request),
    path('friend/friend_request_list', views.list_friend_request),
    
    path('search_target_user', views.search_user), 
    
    path('modify', views.modify_profile)
]
