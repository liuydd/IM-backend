import random
from django.test import TestCase, Client
from board.models import User, UserProfile,Friendship,Label,PrivateChat,Message,Group,FriendRequest,Announcement
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

        #Users:
        self.user = User.objects.create(username="Inion", password="Whatsupbro", email="Oh@My.God")
        self.friend1 = User.objects.create(username="Hentai", password="1145141919810", email="Sen@pa.i")
        self.friend2 = User.objects.create(username="Baka", password="NonNonDayo", email="AijoKaren99@Shengxiang.com")
        self.stranger = User.objects.create(username="Tainaka Ritsu", password="DrumMaster", email="Buqiu@Yingqiu.com")
        self.sendmefriendrequest = User.objects.create(username="Kosaka Honoka", password="12345678")

        #Friendships:
        Friendship.objects.create(user=self.user, friend=self.friend1)
        Friendship.objects.create(user=self.friend1, friend=self.user)
        Friendship.objects.create(user=self.user, friend=self.friend2)
        Friendship.objects.create(user=self.friend2, friend=self.user)

        #Friendrequests:
        FriendRequest.objects.create(sender=self.user,receiver=self.friend1)
        FriendRequest.objects.create(sender=self.friend2,receiver=self.user)
        FriendRequest.objects.create(sender=self.sendmefriendrequest,receiver=self.user)

        #Groups:
        self.groupmembers = list(User.objects.filter(username__in=['Inion','Hentai','Baka','Tainaka Ritsu']))
        self.Mygroup = Group.objects.create(groupname='Dream Team',monitor=self.user)
        for member in self.groupmembers:
            self.Mygroup.members.add(member) 
            member.member_of_group.add(self.Mygroup)
        self.Mygroup.managers.add(self.friend2)
        self.Mygroup.managers.add(self.stranger)
        self.friend2.manage_group.add(self.Mygroup)
        self.stranger.manage_group.add(self.Mygroup)
        self.user.monitor_group.add(self.Mygroup)

        self.bandmates= list(User.objects.filter(username__in=['Inion','Tainaka Ritsu','Kosaka Honoka']))
        self.band=Group.objects.create(groupname='Band',monitor=self.user)
        for member in self.bandmates:
            self.band.members.add(member) 
            member.member_of_group.add(self.band)
        self.user.monitor_group.add(self.band)

        self.idols= list(User.objects.filter(username__in=['Inion','Baka','Kosaka Honoka']))
        self.idolgroup=Group.objects.create(groupname='Idol Group',monitor=self.sendmefriendrequest)
        for member in self.idols:
            self.idolgroup.members.add(member) 
            member.member_of_group.add(self.idolgroup)
        self.idolgroup.managers.add(self.friend2)
        self.friend2.manage_group.add(self.idolgroup)
        self.sendmefriendrequest.monitor_group.add(self.idolgroup)

        #announcements:
        self.announcement = Announcement.objects.create(content='This is a test announcement',author=self.user)
        self.Mygroup.announcements.add(self.announcement)

    #Tests:
    def test_register_new_user(self):
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
        self.assertTrue(User.objects.filter(userid = 1).exists())
        data={'userid':1}
        res = self.client.delete('/delete_user', data =data , content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertFalse(User.objects.filter(userid = 1).exists())

    def test_delete_friend(self):
        self.assertTrue(Friendship.objects.filter(user=self.user, friend=self.friend1).exists())
        data={'userid': 1 ,'friendid': 2 }
        response = self.client.delete('/friends/delete', data=data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Friendship.objects.filter(user=self.user, friend=self.friend1).exists())
    
    def test_label_friend(self):
        data={'userid': 1 ,'friendid': 2 ,'label':'bro'}
        response = self.client.post('/friends/label', data=data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(Label.objects.filter(labelname='bro').exists())

    def test_search_user(self):
        data={'userid': 1 ,'method':'targetname','targetname':'Hentai'}
        response = self.client.get('/search_target_user', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['targetInfo']['username'],'Hentai')

    def test_list_friend(self):
        data={'userid': 1}
        response = self.client.post('/friends/list', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['friendList'][0]['friend'],'Hentai')
        self.assertEqual(response.json()['friendList'][1]['friend'],'Baka')
    

    def test_modify_profile(self):
        data={'userid': 1,'password':'Whatsupbro','newUsername':'','newEmail':'Yoshikawa_Yūko@Kitauji.com','newPhoneNumber':'11100011100','newPassword':'20030415'}
        response = self.client.post('/modify', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(User.objects.filter(username='Inion',email='Yoshikawa_Yūko@Kitauji.com',phone_number='11100011100').exists())

    def test_send_friend_request_stranger(self):
        data={'userid': 1,'friend': 'Tainaka Ritsu'}
        response = self.client.post('/friend/send_friend_request', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(FriendRequest.objects.filter(sender=self.user,receiver=self.stranger).exists())

    def test_send_friend_request_friend_already_send(self):
        data={'userid': 1,'friend': 'Hentai'}
        response = self.client.post('/friend/send_friend_request', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['code'], 1)
        self.assertTrue(FriendRequest.objects.filter(sender=self.user,receiver=self.friend1).exists())

    def test_send_friend_request_to_self(self):
        data={'userid': 1,'friend': 'Inion'}
        response = self.client.post('/friend/send_friend_request', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['code'], 1)
        self.assertFalse(FriendRequest.objects.filter(sender=self.user,receiver=self.user).exists())

    def test_respond_friend_request_already_receive(self):
        data={'userid': 1,'friend': 'Baka'}
        response = self.client.post('/friend/send_friend_request', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(2))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['code'], 1)
        self.assertTrue(FriendRequest.objects.filter(sender=self.friend2,receiver=self.user).exists())
    
    def test_respond_friend_request_accept(self):
        data={'userid': 1,'friend': 'Kosaka Honoka','response':'Accept'}
        response = self.client.post('/friend/respond_friend_request', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(Friendship.objects.filter(user=self.user,friend=self.sendmefriendrequest).exists())
        self.assertTrue(Friendship.objects.filter(user=self.sendmefriendrequest,friend=self.user).exists())

    def test_respond_friend_request_reject(self):
        data={'userid': 1,'friend': 'Kosaka Honoka','response':'rejected'}
        response = self.client.post('/friend/respond_friend_request', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertFalse(Friendship.objects.filter(user=self.user,friend=self.sendmefriendrequest).exists())
        self.assertFalse(Friendship.objects.filter(user=self.sendmefriendrequest,friend=self.user).exists())

    def test_list_friend_request(self):
        data={'userid': 1}
        response = self.client.post('/friend/friend_request_list', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['requestsSent'][0]['sender'],'Inion')
        self.assertEqual(response.json()['requestsReceived'][0]['sender'],'Baka')
        self.assertEqual(response.json()['requestsReceived'][1]['sender'],'Kosaka Honoka')

    def test_create_group(self):
        data={'userid': 1,'members':[1, 2, 3, 4]}
        response = self.client.post('/group/create', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(Group.objects.filter(groupname='Inion, Hentai, Baka, Tainaka Ritsu').exists())
        self.assertTrue(self.user.monitor_group.filter(groupname='Inion, Hentai, Baka, Tainaka Ritsu').exists())

    def test_transfer_monitor_success(self):
        data={'userid': 1,'groupid': 1 ,'newMonitor': 2}
        response = self.client.post('/group/transfer_monitor', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(Group.objects.filter(groupname='Dream Team',monitor=self.friend1).exists())
        self.assertFalse(Group.objects.filter(groupname='Dream Team',monitor=self.user).exists())
        self.assertTrue(self.friend1.monitor_group.filter(groupname='Dream Team').exists())
        self.assertFalse(self.user.monitor_group.filter(groupname='Dream Team').exists())

    def test_Monitor_withdraw_group(self):
        data={'groupid': 1 , 'userid': 1}
        response = self.client.delete('/group/withdraw_group', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertNotEqual(Group.objects.filter(groupname='Dream Team').first().monitor.userid, 1)

    def test_assign_manager_success(self):
        data={'userid': 1,'groupid': 1 ,'newManager': 2}
        response = self.client.post('/group/assign_manager', data = data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertTrue(Group.objects.filter(groupname='Dream Team')[0].managers.contains(self.friend1))

    def test_assign_manager_already(self):
        data={'userid': 1,'groupid': 1 ,'newManager': 3}
        response = self.client.post('/group/assign_manager', data = data, content_type='application/json',HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 1)
    
    def test_list_group(self):
        data = {'userid': 1}
        response = self.client.post('/group/list', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['monitorGroup'][0]['groupname'],'Dream Team')

    def test_remove_member(self):
        data = {'userid': 1,'groupid': 1,'targetid': 4}
        response = self.client.post('/group/remove_member', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertFalse(Group.objects.filter(groupname='Dream Team').first().members.filter(userid=4).exists())

    def test_edit_announcement(self):
        data = {'userid': 1,'groupid': 2,'content': 'New Announcement'}
        response = self.client.post('/group/edit_announcement', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(Group.objects.filter(groupname='Band').first().announcements.first().content,'New Announcement')
    
    def test_list_announcement(self):
        data = {'userid': 1,'groupid': 1}
        response = self.client.post('/group/list_announcement', data = data, content_type='application/json', HTTP_AUTHORIZATION=generate_jwt_token(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['announcements'][0]['content'],'This is a test announcement')
