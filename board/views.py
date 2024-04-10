import json
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes, authentication_classes # login_required
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from .models import Board, User, Friendship, Label, FriendRequest
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, PHONE_NUMBER_LENGTH, CheckRequire, require
from utils.utils_format_check import validate_username, validate_password, validate_email, validate_phone_number
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token


@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")


@CheckRequire
@api_view(["POST"])
def register(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    username = require(body, "username", "string", err_msg="Missing or error type of [username]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    phone_number = require(body, "phoneNumber", "string", err_msg="Missing or error type of [phoneNumber]")
    
    # 检查用户名和密码格式
    invalid_username_msg = validate_username(username)
    if invalid_username_msg:
        return request_failed(2, invalid_username_msg)
    
    invalid_password_msg = validate_password(password)
    if invalid_password_msg:
        return request_failed(2, invalid_password_msg)
    
    # 如提供了email和手机号，则检查格式
    invalid_email_msg = validate_email(email)
    if email and invalid_email_msg:
        return request_failed(2, invalid_email_msg)
    
    invalid_phone_number_msg = validate_phone_number(phone_number)
    if phone_number and invalid_phone_number_msg:
        return request_failed(2, invalid_phone_number_msg)
    
    try:
        User.objects.get(username=username)
        return request_failed(2, "Username already exists", 409)
    except:
        User.objects.create(username=username, password=password, email=email, phone_number=phone_number)
        #User.objects.create(username=username, password=password)
        
        return request_success({"code": 0, "info": "Succeed", "token": generate_jwt_token(username)})


@CheckRequire
@api_view(["POST"])
def user_login(req: HttpRequest):
    # Request body example: {"username": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    username = require(body, "username", "string", err_msg="Missing or error type of [username]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    user = User.objects.filter(username=username, password=password).first()
    
    if user:
        access_token = generate_jwt_token(username)
        return request_success({"code": 0, "info": "Succeed", "token": access_token, "statusCode": 200})
    else:
        return request_failed(2, "Invalid username or password", 401)

#@login_required
#def user_home(req: HttpRequest):




@CheckRequire
def user_logout(req: HttpRequest):
    logout(req)
    return HttpResponse("Logged out successfully")
        
        
def check_for_board_data(body):
    board = require(body, "board", "string", err_msg="Missing or error type of [board]")
    # TODO Start: [Student] add checks for type of boardName and userName
    board_name = require(body, "boardName", "string", err_msg="Missing or error type of [boardName]")
    user_name = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    # TODO End: [Student] add checks for type of boardName and userName
    
    assert 0 < len(board_name) <= 50, "Bad length of [boardName]"
    
    # TODO Start: [Student] add checks for length of userName and board
    assert 0 < len(user_name) <= 50, "Bad length of [userName]"
    assert len(board) == 2500, "Bad length of [board]"
    # TODO End: [Student] add checks for length of userName and board
    
    
    # TODO Start: [Student] add more checks (you should read API docs carefully)
    for i in board:
        assert i == '0' or i == '1', "Invalid value of [board]"
    # TODO End: [Student] add more checks (you should read API docs carefully)
    
    return board, board_name, user_name


@CheckRequire
@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_account(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    username = require(body, "username", "string", err_msg="Missing or error type of [username]")
    user = User.objects.get(username=username)
    user.delete()
    return request_success()


@CheckRequire
def boards(req: HttpRequest):
    if req.method == "GET":
        params = req.GET
        boards = Board.objects.all().order_by('-created_time')
        return_data = {
            "boards": [
                # Only provide required fields to lower the latency of
                # transmitting LARGE packets through unstable network
                return_field(board.serialize(), ["id", "boardName", "createdAt", "userName"]) 
            for board in boards],
        }
        return request_success(return_data)
        
    
    elif req.method == "POST":
        jwt_token = req.headers.get("Authorization")
        body = json.loads(req.body.decode("utf-8"))
        
        # TODO Start: [Student] Finish the board view function according to the comments below
        
        # First check jwt_token. If not exists, return code 2, "Invalid or expired JWT", http status code 401
        decoded_token = check_jwt_token(jwt_token)
        if decoded_token is None:
            return request_failed(2, "Invalid or expired JWT", 401)
        # Then invoke `check_for_board_data` to check the body data and get the board_state, board_name and user_name. 
        # Check the user_name with the username in jwt_token_payload. If not match, return code 3, "Permission denied", http status code 403
        board, board_name, user_name = check_for_board_data(body)
        if user_name != decoded_token["username"]:
            return request_failed(3, "Permission denied", 403)

        # Then invoke `check_for_board_name` to check if the board_name is already used. If yes, return code 4, "Board name already exists", http status code 400
        # if Board.objects.filter(board_name=board_name).first() is not None:
        #    return request_failed(4, "Board name already exists", 400)
        
        # Find the corresponding user instance by user_name. We can assure that the user exists.
        user = User.objects.filter(name=user_name).first()
        
        # We lookup if the board with the same name and the same user exists.
        dest_board = Board.objects.filter(board_name=board_name, user=user).first()
        ## If not exists, new an instance of Board type, then save it to the database.
        if dest_board:
                dest_board.board_state = board
                dest_board.save()
                iscreate = False
        ## If exists, change corresponding value of current `board`, then save it to the database.
        else:
            new_board = Board(board_name=board_name, board_state=board, user=user)
            new_board.save()
            iscreate = True
        
        return request_success({"code": 0, "info": "Succeed", "isCreate": iscreate})
        # TODO End: [Student] Finish the board view function according to the comments above
        
    else:
        return BAD_METHOD
    
    


@CheckRequire
def boards_index(req: HttpRequest, index: any):
    if req.method != "GET" and req.method != "DELETE":
        return BAD_METHOD
    
    idx = require({"index": index}, "index", "int", err_msg="Bad param [id]", err_code=-1)
    if idx < 0:
        return request_failed(-1, "Bad param [id]", 400)
    
    board = Board.objects.filter(id=idx).first()
    if board is None:
        return request_failed(1, "Board not found", 404)
    
    if req.method == "GET": # Return None if not exists
        return request_success(
                return_field(board.serialize(), ["board", "boardName", "userName"])
            )
    
    else:
        # TODO Start: [Student] Finish the board_index view function
        jwt_token = req.headers.get("Authorization")
        decoded_token = check_jwt_token(jwt_token)
        if decoded_token is None:
            return request_failed(2, "Invalid or expired JWT", status_code=401)
        
        if board.user.name != decoded_token["username"]:
            return request_failed(3, "Cannot delete board of other users", status_code=403)
        
        board.delete()
        return request_success({"code": 0, "info": "Succeed"})
        # TODO End: [Student] Finish the board_index view function
    


# TODO Start: [Student] Finish view function for user_board
def user_board(req: HttpRequest, username: any):
    if req.method != "GET":
        return BAD_METHOD
    
    assert (username is not None) and (0 < len(str(username)) <= 50), request_failed(-1, "Bad param [userName]", status_code=400)
    
    try:
        user = User.objects.get(name=username)
        board = Board.objects.filter(user=user)
        return request_success({
            "code": 0,
            "info": "Succeed",
            "userName": username,
            "boards": [return_field(b.serialize(), ["id", "boardName", "createdAt", "userName"]) for b in board]
        }
        )
    except:
        return request_failed(1, "User not found", status_code=404)
# TODO End: [Student] Finish view function for user_board


@CheckRequire
@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_friend(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    friend = body["friend"]
    username = body["username"]
    try:
        user = User.objects.get(username=username)
        friend = User.objects.get(username=friend)
        friendship = Friendship.objects.get(user=user, friend=friend)
        friendship.delete()
        return request_success({"code": 0, "info": "Success"})
    except:
        return request_failed(1, "Target user not in friend list", status_code=404)
    
@CheckRequire
@api_view(["POST"])
def label_friend(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    
    user = User.objects.get(username=body["username"])
    friend = User.objects.get(username=body["friend"])
    friendship = Friendship.objects.get(user=user, friend=friend)
    
    try:
        friendship.labels.get(labelname=body["label"])
        return request_failed(1, "Label already exists", status_code=400)
    except: 
        new_label = Label.objects.create(labelname=body["label"])
        friendship.labels.add(new_label)
        return request_success({"code": 0, "info": "Success"})
    
    
@CheckRequire
@api_view(["GET"])
def search_user(req: HttpRequest):
    
    method_used = req.GET["method"]
    
    if method_used == "targetname":
        target = User.objects.filter(username=req.GET["targetname"]).first()
    elif method_used == "email":
        target = User.objects.filter(email=req.GET["email"]).first()
    elif method_used == "phoneNumber":
        target = User.objects.filter(phone_number=req.GET["phoneNumber"]).first()
    
    if not target:
        return request_failed(1, "User not found", status_code=404)
    
    return request_success({
            "code": 0,
            "info": "Succeed",
            "targetInfo": return_field(target.serialize(), ["username", "email", "phoneNumber"]) 
        }
        )
    
    
@CheckRequire
@api_view(["POST"])
def list_friend(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    
    friendships = Friendship.objects.filter(user=user)
    
    if not friendships.exists():
        return request_failed(1, "No friend", status_code=404)
   
    return request_success({
        "code": 0,
        "info": "Succeed",
        "friendList": [friendship.serialize() for friendship in friendships]
    })
    
    
@CheckRequire
@api_view(["POST"])
def modify_profile(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    password = body["password"]
    
    if user.password != password:
        return request_failed(1, "Wrong password", status_code=404)
    
    if body["newPassword"]:
        user.password = body["newPassword"]
    if body["newEmail"]:
        user.email = body["newEmail"]
    if body["newPhoneNumber"]:
        user.phone_number = body["newPhoneNumber"]
    
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    



@CheckRequire
@api_view(["POST"])
def send_friend_request(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    friend = User.objects.get(username=body["friend"])
    
    # 双方已是好友
    if Friendship.objects.filter(user=user, friend=friend).exists():
        return request_failed(1, "Already friends", status_code=404)
    
    # 向自己发送好友请求
    if user == friend:
        return request_failed(1, "Cannot send friend request to yourself", status_code=404)
    
    # 向同一用户发送过好友请求
    if FriendRequest.objects.filter(sender=user, receiver=friend, response_status="pending").exists():
        return request_failed(1, "Already sent friend request", status_code=404)
    
    # 对方向你发送过好友请求
    if FriendRequest.objects.filter(sender=friend, receiver=user, response_status="pending").exists():
        return request_failed(1, "Please directly respond to the request sent by the target user", status_code=404)
    
    
    FriendRequest.objects.create(sender=user, receiver=friend)
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    
    
@CheckRequire
@api_view(["POST"])
def respond_friend_request(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    friend = User.objects.get(username=body["friend"])
    friend_request = FriendRequest.objects.get(sender=friend, receiver=user)
    
    if body["response"] == "Accept":
        friend_request.response_status = "accepted"
        friend_request.save()
        Friendship.objects.create(user=user, friend=friend)
        Friendship.objects.create(user=friend, friend=user)
        return request_success({
            "code": 0,
            "info": "Succeed"
        })
        
    else:
        friend_request.response_status = "rejected"
        friend_request.save()
        return request_success({    
            "code": 0,
            "info": "Succeed"
        })
        
        
@CheckRequire
@api_view(["POST"])
def list_friend_request(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    requests_sent = FriendRequest.objects.filter(sender=user)
    requests_received = FriendRequest.objects.filter(receiver=user)
    return request_success({
        "requestsSent": [
            return_field(request.serialize(), ["sender", "receiver", "timestamp"])
            for request in requests_sent
        ],
        "requestsReceived": [
            return_field(request.serialize(), ["sender", "receiver", "timestamp"])
            for request in requests_received
        ]
    })