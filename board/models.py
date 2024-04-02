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
        boards = Board.objects.filter(user=self)
        return {
            "userid": self.userid, 
            "username": self.username, 
            "created_time": self.created_time,
            "boards": [ return_field(board.serialize(), ["id", "boardName", "username", "createdAt"])
                       for board in boards ]
        }
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    friends = models.ManyToManyField(User, blank=True, related_name="friend")
    groups = models.ManyToManyField('Group', blank=True)
    
    
class Friendship(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends1")  
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends2')
    
    class Meta:
        unique_together = ('user1', 'user2')  
    

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
    members = models.ManyToManyField(UserProfile, blank=True)
    







class Board(models.Model):
    # TODO Start: [Student] Finish the model of Board
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board_state = models.CharField(max_length=MAX_CHAR_LENGTH)
    board_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    
    class Meta:
        indexes = [models.Index(fields=["board_name"])]
        unique_together = ("user", "board_name")
    # Meta data
    # Create index on board_name
    # Create unique_together on user and board_name
    
    # TODO End: [Student] Finish the model of Board


    def serialize(self):
        userName = self.user.name
        return {
            "id": self.id,
            "board": self.board_state, 
            "boardName": self.board_name,
            "userName": userName,
            "createdAt": self.created_time
        }

    def __str__(self) -> str:
        return f"{self.user.name}'s board {self.board_name}"
