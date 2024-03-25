from django.urls import path, include
from . import views

urlpatterns = [
    path('startup', views.startup),
    path('login', views.login),
    path('boards', views.boards),
    # TODO Start: [Student] add routing paths for `boards/<index>` and `user/<userName>`
    path('boards/<index>', views.boards_index),
    path('user/<username>', views.user_board)
    # TODO End: [Student] add routing paths for `boards/<index>` and `user/<userName>`
]
