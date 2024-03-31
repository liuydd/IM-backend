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
            "createdAt": self.created_time,
            "boards": [ return_field(board.serialize(), ["id", "boardName", "username", "createdAt"])
                       for board in boards ]
        }
    
    def __str__(self) -> str:
        return self.username


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
