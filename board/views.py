import json
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes, authentication_classes # login_required
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from .models import User, Friendship, Label, FriendRequest, Group
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, PHONE_NUMBER_LENGTH, CheckRequire, require
from utils.utils_format_check import validate_username, validate_password, validate_email, validate_phone_number
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token


@CheckRequire
@api_view(["POST"])
def register(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
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
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    username = require(body, "username", "string", err_msg="Missing or error type of [username]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    user = User.objects.filter(username=username, password=password).first()
    
    if user:
        access_token = generate_jwt_token(username)
        return request_success({"code": 0, "info": "Succeed", "token": access_token, "statusCode": 200})
    else:
        return request_failed(2, "Invalid username or password", 401)

@CheckRequire
def user_logout(req: HttpRequest):
    logout(req)
    return HttpResponse("Logged out successfully")


@CheckRequire
@api_view(["DELETE"])
def delete_account(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD 
    user = User.objects.get(username=req.username)
    user.delete()
    return request_success({"code": 0, "info": "Succeed"})


@CheckRequire
@api_view(["DELETE"])
def delete_friend(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    friend = body["friend"]
    username = body["username"]
    try:
        user = User.objects.get(username=username)
        friend = User.objects.get(username=friend)
        friendship = Friendship.objects.get(user=user, friend=friend)
        friendship.delete()
        friendship = Friendship.objects.get(user=friend, friend=user)
        friendship.delete()
        return request_success({"code": 0, "info": "Success"})
    except:
        return request_failed(1, "Target user not in friend list", status_code=404)
    
@CheckRequire
@api_view(["POST"])
def label_friend(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
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
    if req.method != "GET":
        return BAD_METHOD
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
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    
    friendships = Friendship.objects.filter(user=user)
    
    if not friendships.exists():
        return request_failed(1, "No friend", status_code=404)
   
    return request_success({
        "code": 0,
        "info": "Succeed",
        "friendList": [return_field(friendship.serialize(), ["friend", "labels"]) for friendship in friendships]
    })
    
    
@CheckRequire
@api_view(["POST"])
def modify_profile(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
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
    
    user.save()
    
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    



@CheckRequire
@api_view(["POST"])
def send_friend_request(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
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
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    friend = User.objects.get(username=body["friend"])
    friend_request = FriendRequest.objects.get(sender=friend, receiver=user, response_status="pending")
    
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
    if req.method != "POST":
        return BAD_METHOD
    
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    requests_sent = FriendRequest.objects.filter(sender=user)
    requests_received = FriendRequest.objects.filter(receiver=user)
    return request_success({
        "requestsSent": [
            return_field(request.serialize(), ["sender", "receiver", "timestamp", "responseStatus"])
            for request in requests_sent
        ],
        "requestsReceived": [
            return_field(request.serialize(), ["sender", "receiver", "timestamp", "responseStatus"])
            for request in requests_received
        ]
    })

@CheckRequire
@api_view(["POST"])
def create_group(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    members = [User.objects.get(username=i) for i in body["members"]]
    groupname = ", ".join(body["members"])
    new_group = Group.objects.create(monitor=user, groupname=groupname)
    for i in members:
        new_group.members.add(i)
    return request_success({
        "code": 0, 
        "info": "Group created successfully"
    })
  
    
@CheckRequire
@api_view(["POST"])
def transfer_monitor(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    new_monitor = User.objects.get(username=body["newMonitor"])
    group = Group.objects.get(groupid=body["groupid"])
    if group.monitor != User.objects.get(username=body["username"]):
        
        return request_failed(1, "You are not the monitor of this group", status_code=404)
    if new_monitor not in group.members.all():
        return request_failed(1, "The new monitor is not in the group", status_code=404)
    else:
        group.monitor = new_monitor
    group.save()
    
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    

def withdraw_group(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    group = Group.objects.get(groupid=body["groupid"])
    if group.monitor == User.objects.get(username=body["username"]):
        group.members.remove(group.monitor)
        if group.managers.exists():
            group.monitor = group.managers.first()
            group.managers.remove(group.monitor)
        else:
            if group.members.exists():
                group.monitor = group.members.first()
            else:
                group.delete()
    elif group.managers.filter(username=body["username"]).exists():
        group.managers.remove(User.objects.get(username=body["username"]))
        group.members.remove(User.objects.get(username=body["username"]))
    else:
        group.members.remove(User.objects.get(username=body["username"]))
    group.save()

    return request_success({
        "code": 0,
        "info": "Succeed"
    })


def assign_managers(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    group = Group.objects.get(groupid=body["groupid"])
    group.managers.add(*[User.objects.get(username=i) for i in body["managers"]])
    group.save()

    return request_success({
        "code": 0,
        "info": "Succeed"
    })

def list_group(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    monitor_group = [group.serialize() for group in user.monitor_group.all()]
    manage_group = [group.serialize() for group in user.manage_group.all()]
    member_of_group = [group.serialize() for group in user.member_of_group.all()]
    return request_success({
        "code": 0,
        "info": "Group list retrieved successfully",
        "monitorGroup": monitor_group,
        "manageGroup": manage_group,
        "memberOfGroup": member_of_group
    })

def assign_manager(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    group = Group.objects.get(groupid=body["groupid"])
    user = User.objects.get(username=body["username"])
    target = User.objects.get(username=body["target"])
    
    if group.monitor != user:
        return request_failed(1, "You are not the monitor of this group")
    
    if target == user:
        return request_failed(1, "You are already the monitor of this group")
    
    if group.managers.contains(target):
        return request_failed(1, "This user is already a manager")
    
    group.managers.add(target)
    group.members.remove(target)
    group.save()

    return request_success({
        "code": 0,
        "info": "Succeed"
    })


def remove_member(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(username=body["username"])
    group = Group.objects.get(groupid=body["groupid"])
    target = User.objects.get(username=body["target"])
    
    if user == target:
        return request_failed(1, "You cannot remove yourself")
    
    if group.monitor == user:
        if group.managers.contains(target):
            group.managers.remove(target)
        else:
            group.members.remove(target)
        group.save()
    
    elif group.managers.contains(user):
        if group.monitor == target or group.managers.contains(target):
            return request_failed(1, "You cannot remove a monitor or a manager")
        else:
            group.members.remove(target)
        group.save()
    
    else:
        return request_failed(1, "You are not allowed to kick anyone out of group")
    