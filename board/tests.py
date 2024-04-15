import random
from django.test import TestCase, Client
from board.models import User, UserProfile,Friendship,Label,PrivateChat,Message,Group,FriendRequest
import datetime
import hashlib
import hmac
import time
import json
import base64
from utils.utils_jwt import EXPIRE_IN_SECONDS, SALT, b64url_encode

class BoardTests(TestCase):
    # Initializer
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="Inion", password="Whatsupbro", email="Oh@My.God")
        self.friend1 = User.objects.create(username="Hentai", password="1145141919810", email="Sen@pa.i")
        self.friend2 = User.objects.create(username="Baka", password="NonNonDayo", email="AijoKaren99@Shengxiang.com")
        Friendship.objects.create(user=self.user, friend=self.friend1)
        Friendship.objects.create(user=self.friend1, friend=self.user)
        Friendship.objects.create(user=self.user, friend=self.friend2)
        Friendship.objects.create(user=self.friend2, friend=self.user)
        
    # ! Utility functions
    def generate_jwt_token(self, username: str, payload: dict, salt: str):
        # * header
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        # dump to str. remove `\n` and space after `:`
        header_str = json.dumps(header, separators=(",", ":"))
        # use base64url to encode, instead of base64
        header_b64 = b64url_encode(header_str)
        
        # * payload
        payload_str = json.dumps(payload, separators=(",", ":"))
        payload_b64 = b64url_encode(payload_str)
        
        # * signature
        signature_str = header_b64 + "." + payload_b64
        signature = hmac.new(salt, signature_str.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signature_b64 = b64url_encode(signature)
        
        return header_b64 + "." + payload_b64 + "." + signature_b64

    
    def generate_header(self, username: str, payload: dict = {}, salt: str = SALT):
        if len(payload) == 0:
            payload = {
                "iat": int(time.time()),
                "exp": int(time.time()) + EXPIRE_IN_SECONDS,
                "data": {
                    "username": username
                }
            }
        return {
            "HTTP_AUTHORIZATION": self.generate_jwt_token(username, payload, salt)
        }

    def post_board(self, board_state, board_name, user_name, headers):
        payload = {
            "board": board_state,
            "boardName": board_name,
            "username": user_name
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/boards", data=payload, content_type="application/json", **headers)

    def get_board_index(self, index):
        return self.client.get(f"/boards/{index}")
    
    def delete_board_index(self, index, headers):
        return self.client.delete(f"/boards/{index}", **headers)


    # ! Test section
    
    # * Tests for login view
    
    
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
        res = self.client.delete('/delete_user', {'username': 'Inion'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertFalse(User.objects.filter(username='Inion').exists())

    def test_delete_friend(self):
        self.assertTrue(Friendship.objects.filter(user=self.friend1, friend=self.user).exists())
        self.assertTrue(Friendship.objects.filter(user=self.user, friend=self.friend1).exists())
        response = self.client.delete('/delete_friend', {'username': 'Hentai'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Friendship.objects.filter(user=self.friend1, friend=self.user).exists())
        self.assertFalse(Friendship.objects.filter(user=self.user, friend=self.friend1).exists())
    
    def test_label_friend(self):
        response = self.client.post('/friends/label', {'username': 'Inion'},format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(len(response.json()['friendList']), 2)
        self.assertEqual(response.json()['friendList'][0]['username'], 'Hentai')
        self.assertEqual(response.json()['friendList'][1]['username'], 'Baka')
        self.assertTrue(Label.objects.filter(labelname='Hentai').exists())

    def test_search_user(self):
        response = self.client.get('/search_target_user', params={'username': 'Inion', 'method': 'targetname'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['info'], 'Succeed')
        targetInfo = response.json()['targetInfo']
        self.assertEqual(targetInfo['username'], 'Inion')
        self.assertEqual(targetInfo['email'], 'Oh@My.God')
