from utils import utils_time
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

# Create your models here.

class User(models.Model):
    userid = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    email = models.CharField(max_length=MAX_CHAR_LENGTH, blank=True)
    phone_number = models.CharField(max_length=MAX_CHAR_LENGTH, blank=True)
    
    class Meta:
        indexes = [models.Index(fields=["username"])]
        
    def serialize(self):
        return {
            "userid": self.userid, 
            "username": self.username,
            "email": self.email,
            "phoneNumber": self.phone_number
        }
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    friends = models.ManyToManyField(User, blank=True, related_name="friend")
    groups = models.ManyToManyField('Group', blank=True)
    
    
class Label(models.Model):
    labelname = models.CharField(max_length=MAX_CHAR_LENGTH)
    
    def __str__(self):
        return self.labelname
    
class Friendship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_as_user')  
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_as_friend')
    labels = models.ManyToManyField(Label, blank=True)
    
    class Meta:
        unique_together = ('user', 'friend')  
    
    def serialize(self):
        return {
            "friend": self.friend.username,
            "labels": list(self.labels.values_list('labelname', flat=True))
        }
    

class PrivateChat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="private_chat_1")
    user2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="private_chat_2")
    messages = models.ManyToManyField('Message', blank=True)

    
class Message(models.Model):
    msgid = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="received_messages")
    private_chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name="private_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    
class Group(models.Model):
    groupid = models.BigAutoField(primary_key=True)
    groupname = models.CharField(max_length=MAX_CHAR_LENGTH)
    monitor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="monitor_group")
    managers = models.ManyToManyField(User, blank=True, related_name="manage_group")
    members = models.ManyToManyField(User, blank=True)
    announcements = models.ManyToManyField('Announcement', blank=True)
    
    def serialize(self):
        return {
            "groupid": self.groupid,
            "groupname": self.groupname,
            "monitor": self.monitor,
            "managers": list(self.managers.values_list('username', flat=True)),
            "members": list(self.members.values_list('user__username', flat=True))
        }
    

class FriendRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_friend_requests")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_friend_requests")
    timestamp = models.DateTimeField(auto_now_add=True)
    response_status = models.CharField(max_length=MAX_CHAR_LENGTH, default="pending")
    
    def serialize(self):
        return {
            "id": self.id,
            "sender": self.sender.username,
            "receiver": self.receiver.username,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "responseStatus": self.response_status
        }
        

class Announcement(models.Model):
    id = models.BigAutoField(primary_key=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def serialize(self):
        return {
            "content": self.content,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
