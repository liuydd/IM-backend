import random
from django.test import TestCase, Client
from board.models import User, UserProfile,Friendship,Label,PrivateChat,Message,Group,FriendRequest
import datetime
import hashlib
import hmac
import time
import json
import base64
from utils.utils_jwt import generate_jwt_token

class BoardTests(TestCase):
    # Initializer
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="Inion", password="Whatsupbro", email="Oh@My.God")
        self.friend1 = User.objects.create(username="Hentai", password="1145141919810", email="Sen@pa.i")
        self.friend2 = User.objects.create(username="Baka", password="NonNonDayo", email="AijoKaren99@Shengxiang.com")
        Friendship.objects.create(user=self.user, friend=self.friend1)
        Friendship.objects.create(user=self.user, friend=self.friend2)
        
    # Test cases
    def test_register_new_user(self):
        # assert(User.objects.filter(username="Ashitu").count() == 0
        data = {"username": "newuser", "password": "12345678", "email": "", "phoneNumber": ""}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertTrue(res.json()['token'].count('.') == 2)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        
    def test_register_new_user_with_email_but_wrong(self):
        data = {"username": "newuser1", "password": "12345678", "email": "wrongemail", "phoneNumber": ""}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 2)
        self.assertFalse(User.objects.filter(username="newuser1").exists())
    
    def test_register_new_user_with_phone_number_but_wrong(self):
        data = {"username": "newuser2", "password": "12345678", "email": "", "phoneNumber": "wrongphonenumber"}
        res = self.client.post('/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 2)
        self.assertFalse(User.objects.filter(username="newuser2").exists())

    def test_login_existing_user_correct_password(self):
        self.assertTrue(User.objects.filter(username="Inion").exists())
        data = {"username": "Inion", "password": "Whatsupbro"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertTrue(res.json()['token'].count('.') == 2)

    def test_login_existing_user_wrong_password(self):
        data = {"username": "Inion", "password": "Damnitman"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)

    def test_login_non_existing_user(self):
        data = {"username": "GirlFriend", "password": "5201314www"}
        res = self.client.post('/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)
    
    def test_delete_user(self):
        self.assertTrue(User.objects.filter(username='Inion').exists())
        data={'username':'Inion'}
        res = self.client.delete('/delete_user', data=data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token('Inion'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertFalse(User.objects.filter(username='Inion').exists())

    def test_delete_friend(self):
        self.assertTrue(Friendship.objects.filter(user=self.user, friend=self.friend1).exists())
        data={'username':'Inion','friend':'Hentai'}
        response = self.client.delete('/friends/delete', data=data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token('Inion'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Friendship.objects.filter(user=self.user, friend=self.friend1).exists())
    
    def test_label_friend(self):
        data={'username':'Inion','friend':'Hentai','label':'bro'}
        response = self.client.post('/friends/label', data=data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token('Inion'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(Label.objects.filter(labelname='bro').exists())

