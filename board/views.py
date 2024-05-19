import re
import json
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view # login_required
from rest_framework.response import Response

from .models import User, Friendship, Label, FriendRequest, Group, Announcement, Invitation, Message, Conversation
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_ANNOUNCEMENT_LENGTH, CheckRequire, require
from utils.utils_format_check import validate_username, validate_password, validate_email, validate_phone_number
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token

from datetime import datetime, timezone
from typing import Dict, Any
from django.views.decorators.http import require_http_methods
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


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
        user = User.objects.create(username=username, password=password, email=email, phone_number=phone_number)
        
        return request_success({"code": 0, "info": "Succeed", "token": generate_jwt_token(username), "userid": user.userid})

def check_password(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    userid = body["userid"]
    password = body["password"]
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    user = User.objects.filter(userid = userid, password=password).first()
    if user:
        return request_success({"code": 0, "info": "Succeed"})
    else:
        return request_failed(2, "Invalid username or password", 401)
    
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
        access_token = generate_jwt_token(user.userid)
        return request_success({"code": 0, "info": "Succeed", "token": access_token, "statusCode": 200, "userid": user.userid})
    else:
        return request_failed(2, "Invalid username or password", 401)

@CheckRequire
def user_logout(req: HttpRequest):
    logout(req)
    return HttpResponse("Logged out successfully")


@CheckRequire
def delete_account(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD 
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    user.delete()
    return request_success({"code": 0, "info": "Succeed"})


@CheckRequire
def delete_friend(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    friendid = body["friendid"]
    userid = body["userid"]
    try:
        user = User.objects.get(userid=userid)
        friend = User.objects.get(userid=friendid)
        friendship = Friendship.objects.get(user=user, friend=friend)
        friendship.delete()
        friendship = Friendship.objects.get(user=friend, friend=user)
        friendship.delete()
        members = [user, friend]
        convo = Conversation.objects.filter(members__in=members, type='private_chat').prefetch_related('members').distinct().first()
        convo.delete()
        return request_success({"code": 0, "info": "Success"})
    except:
        return request_failed(1, "Target user not in friend list", status_code=404)
    
@CheckRequire
def label_friend(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    friend = User.objects.get(userid=body["friendid"])
    friendship = Friendship.objects.get(user=user, friend=friend)
    
    try:
        friendship.labels.get(labelname=body["label"])
        return request_failed(1, "Label already exists", status_code=400)
    except: 
        new_label = Label.objects.create(labelname=body["label"])
        friendship.labels.add(new_label)
        return request_success({"code": 0, "info": "Success"})
    
    
@CheckRequire
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
            "targetInfo": return_field(target.serialize(), ["userid", "username", "email", "phoneNumber"]) 
        })
    
    
@CheckRequire
def list_friend(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    
    friendships = Friendship.objects.filter(user=user)
    
    if not friendships.exists():
        return request_failed(1, "No friend", status_code=404)
   
    return request_success({
        "code": 0,
        "info": "Succeed",
        "friendList": [return_field(friendship.serialize(), ["friendid", "friend", "labels"]) for friendship in friendships]
    })
    
    
@CheckRequire
def modify_profile(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    password = body["password"]
    if user.password != password:
        return request_failed(1, "Wrong password", status_code=404)
    
    if body["newUsername"]:
        user.username = body["newUsername"]
    if body["newPassword"]:
        user.password = body["newPassword"]
    if body["newEmail"]:
        user.email = body["newEmail"]
    if body["newPhoneNumber"]:
        user.phone_number = body["newPhoneNumber"]
    if body["newAvatar"]:
        user.avatar = body["newAvatar"]
    
    user.save()

    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    

@CheckRequire
def send_friend_request(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
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
def respond_friend_request(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
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
def list_friend_request(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
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
def create_group(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    members = [User.objects.get(userid=i) for i in body["members"]]
    groupname = ", ".join([member.username for member in members])
    new_group = Group.objects.create(monitor=user, groupname=groupname)
    for i in members:
        new_group.members.add(i)
    new_group.members.add(user)
    return request_success({
        "code": 0, 
        "info": "Group created successfully"
    })
  
    
@CheckRequire
def transfer_monitor(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    new_monitor = User.objects.get(userid=body["newMonitor"])
    group = Group.objects.get(groupid=body["groupid"])
    if group.monitor != user:   
        return request_failed(1, "You are not the monitor of this group", status_code=404)
    if user == new_monitor:
        return request_failed(1, "The new monitor is the same as the current monitor", status_code=404)
    if new_monitor not in group.members.all():
        return request_failed(1, "The new monitor is not in the group", status_code=404)
    if new_monitor in group.managers.all():
        group.managers.remove(new_monitor)
    group.monitor = new_monitor
    group.save()
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    

@CheckRequire
def withdraw_group(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    group = Group.objects.get(groupid=body["groupid"])
    user = User.objects.get(userid=body["userid"])
    group.members.remove(user)
    if group.monitor == user:
        if group.managers.exists():
            group.monitor = group.managers.first()
            group.managers.remove(group.monitor)
            group.save()
        else:
            if group.members.exists():
                group.monitor = group.members.first()
                group.save()
            else:
                group.delete()
    elif group.managers.contains(user):
        group.managers.remove(user)
    group.save()

    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    

@CheckRequire
def assign_manager(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    group = Group.objects.get(groupid=body["groupid"])
    user = User.objects.get(userid=body["userid"])
    new_manager = User.objects.get(userid=body["newManager"])
    if group.monitor != user:
        return request_failed(1, "You are not the monitor of this group, so you cannot assign managers")
    if group.monitor == new_manager:
        return request_failed(1, "The target user is the monitor of the group, so you cannot assign him/her as a manager")
    if group.managers.contains(new_manager):
        return request_failed(1, "The target user is already one of the managers")

    group.managers.add(new_manager)
    group.save()

    return request_success({
        "code": 0,
        "info": "Succeed"
    })


@CheckRequire
def list_group(req: HttpRequest):
    user = User.objects.get(userid=req.GET["userid"])
    member = user.member_of_group.all()
    real = []
    for group in member:
        if group.monitor == user or group.managers.contains(user):
            continue
        real.append(group)
    return request_success({
        "code": 0,
        "info": "Group list retrieved successfully",
        "monitorGroup": [group.serialize() for group in user.monitor_group.all()],
        "manageGroup": [group.serialize() for group in user.manage_group.all()],
        "memberOfGroup": [group.serialize() for group in real]
    })


@CheckRequire
def remove_member(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    group = Group.objects.get(groupid=body["groupid"])
    target = User.objects.get(userid=body["targetid"])
    
    if user == target:
        return request_failed(1, "You cannot remove yourself")
    
    if group.monitor == user:
        if group.managers.contains(target):
            group.managers.remove(target)
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
    
    return request_success({
        "code": 0,
        "info": "Succeed"
    })

@CheckRequire
def list_announcement(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    group = Group.objects.get(groupid=body["groupid"])

    if not group.members.contains(user):
        return request_failed(1, "You are not a member of this group")

    announcements = Announcement.objects.filter(group=group)
    return request_success({
        "code": 0,
        "info": "Succeed",
        "announcements": [announcement.serialize() for announcement in announcements]
    })

@CheckRequire
def post_announcement(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    group = Group.objects.get(groupid=body["groupid"])
    if group.monitor != user and user not in group.managers.all():
        return request_failed(1, "You don't have the permission to edit the announcement")
    group.announcements.add(Announcement.objects.create(author=user, content=body["content"]))
    group.save()
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    
def send_invitation(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    userid = body["userid"]
    groupid = body["groupid"]
    friendid = body["friendid"]
    user = User.objects.get(userid=userid)
    group = Group.objects.get(groupid=groupid)
    friend = User.objects.get(userid=friendid)
    if group.members.contains(friend):
        return request_failed(1, "This user is already a member of this group")
    
    if group.monitor == user or group.managers.contains(user):
        group.members.add(friend)
    else:
        Invitation.objects.create(sender=user, receiver=friend, group=group)
    
    return request_success({
        "code": 0,
        "info": "Succeed"
    })

def get_invitation(req: HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    userid = body["userid"]
    groupid = body["groupid"]
    user = User.objects.get(userid=userid)
    group = Group.objects.get(groupid=groupid)
    
    if group.monitor == user or group.managers.contains(user):
        invitations = Invitation.objects.filter(group=group)
        return request_success({
            "code": 0,
            "info": "Succeed",
            "invitations": [invitation.serialize() for invitation in invitations]
        })
    else:
        return request_failed(1, "You are not allowed to get invitations")
    
def process_invitation(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    response = body["response"]
    invitation = Invitation.objects.get(id=body["invitationid"])
    if response == "Accept":
        target = invitation.receiver
        group = invitation.group
        group.members.add(target)
    
    invitation.delete()
    return request_success({
        "code": 0,
        "info": "Succeed"
    })
    
def delete_message(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    body = json.loads(req.body.decode("utf-8"))
    user = User.objects.get(userid=body["userid"])
    message = Message.objects.get(id=body["messageid"])
    message.receivers.remove(user)
    return request_success({
        "code": 0,
        "info": "Succeed"
    })

# Create your views here.
@require_http_methods(["DELETE", "POST", "GET"])
def messages(request: HttpRequest) -> HttpResponse: 
    if request.method == "DELETE":
        # data = json.loads(request.data)
        # message_id = data.get('message_id')
        # username = data.get('username')
        message_id = request.GET.get('message_id')
        username = request.GET.get('username')
        m = Message.objects.get(id=message_id)
        m.receivers.remove(User.objects.get(username=username))
        return request_success({"code": 0, "info": "Succeed"})
        
    elif request.method == "POST":
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        # sender_userid = data.get('userid')
        content = data.get('content', '')
        respond_target = data.get('target', '')
        sender_username = data.get('username')

        # 验证 conversation_id 和 sender_username 的合法性
        try:
            conversation = Conversation.objects.prefetch_related('members').get(id=conversation_id) 
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)

        try:
            # sender = User.objects.get(userid=sender_userid)
            sender = User.objects.get(username=sender_username)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid userid'}, status=400)

        # 验证 sender 是否是 conversation 的成员
        if not conversation.members.contains(sender):
            return JsonResponse({'error': 'Sender is not a member of the conversation'}, status=403)
        if respond_target:
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                reply_to_id=respond_target,
            )
        else:
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                # reply_to_id=respond_target,
            )
        # print(respond_target)
        message.receivers.set(conversation.members.all())
        
        message.already_read.add(sender)
        message.save()
        
        if respond_target:
            target = Message.objects.get(id=int(respond_target))
            message.reply_to_id = int(respond_target)
            target.response_count += 1
            target.save()
        # print(target.response_count)
        # if respond_target:
        #     target = Message.objects.get(id=int(respond_target))
        #     message.reply_to_id = int(respond_target)
        #     target.response_count += 1
        #     target.save()

        channel_layer = get_channel_layer()
        for member in conversation.members.all():
            async_to_sync(channel_layer.group_send)(member.username, {'type': 'notify'})

        return JsonResponse(format_message(message), status=200)

    elif request.method == "GET":
        # userid: str = request.GET.get('userid')
        username: str = request.GET.get('username')
        conversation_id: str = request.GET.get('conversation_id')
        after: str = request.GET.get('after', '0')
        after_datetime = datetime.fromtimestamp((int(after) + 1) / 1000.0, tz=timezone.utc)
        limit: int = int(request.GET.get('limit', '100'))

        messages_query = Message.objects.filter(timestamp__gte=after_datetime).order_by('timestamp')
        messages_query = messages_query.prefetch_related('conversation')

        # if userid:
        #     try:
        #         userid = int(userid)
        #         user = User.objects.get(userid=userid)
        #         messages_query = messages_query.filter(receivers=user)
        #     except User.DoesNotExist:
        #         return JsonResponse({'messages': [], 'has_next': False}, status=200)
        if username:
            try:
                user = User.objects.get(username=username)
                messages_query = messages_query.filter(receivers=user)
            except User.DoesNotExist:
                return JsonResponse({'messages': [], 'has_next': False}, status=200)
        elif conversation_id:
            try:
                conversation_id = int(conversation_id)
                conversation = Conversation.objects.get(id=conversation_id)
                messages_query = messages_query.filter(conversation=conversation)
            except Conversation.DoesNotExist:
                return JsonResponse({'messages': [], 'has_next': False}, status=200)
        else:
            return JsonResponse({'error': 'Either userid or conversation ID must be specified'}, status=400)
        
        messages = list(messages_query[:limit+1])
        messages_data = [format_message(message) for message in messages]

        # 检查是否还有更多消息
        has_next = False
        if len(messages_data) > limit:
            has_next = True
            messages_data = messages_data[:limit]
            
        for message in messages:
            if not message.already_read.contains(user):
                message.already_read.add(user)

        return JsonResponse({'messages': messages_data, 'has_next': has_next}, status=200)

# @require_http_methods(["POST", "GET"])
def conversations(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        data = json.loads(request.body)
        conversation_type = data.get('type')
        membernames_ = data.get('members', [])

        membernames = []

        for m in membernames_:
            if m not in membernames:
                membernames.append(m)

        members = []
        for username in membernames:
            try:
                members.append(User.objects.get(username=username))
            except User.DoesNotExist:
                return JsonResponse({'error': f'Invalid username: {username}'}, status=400)

        if conversation_type == 'group_chat':
            if len(membernames) < 3:
                return JsonResponse({'error': f'Invalid member count'}, status=400)
        else:
            if len(members) != 2:
                return JsonResponse({'error': f'Invalid member count'}, status=400)
            # 检查是否已存在私人聊天
            existing_conversations = Conversation.objects.filter(members__in=members, type='private_chat').prefetch_related('members').distinct()
            for conv in existing_conversations:
                if conv.members.count() == 2 and set(conv.members.all()) == set(members):
                    # 找到了一个已存在的私人聊天，直接返回
                    return JsonResponse(format_conversation(conv), status=200)
        conversation = Conversation.objects.create(type=conversation_type)
        conversation.members.set(members)
        return JsonResponse(format_conversation(conversation), status=200)

    if request.method != "GET":
        return BAD_METHOD
    
    conversation_ids = request.GET.getlist('id', [])
    valid_conversations = Conversation.objects.filter(id__in=conversation_ids).prefetch_related('members')
    response_data = [format_conversation(conv) for conv in valid_conversations]
    return JsonResponse({'conversations': response_data, 'code': 0, 'info': 'Success'}, status=200)


def filter_messages(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    
    # userid = int(req.GET.get('userid'))
    username = req.GET.get('username')
    user = User.objects.get(username=username)
    conversation_id = int(req.GET.get('conversationId'))
    convo = Conversation.objects.get(id=conversation_id)
    if user not in convo.members.all():
        return JsonResponse({'error': 'User is not a member of the conversation'}, status=403)
    
    sender = req.GET.get('sendername', '')
    start_time = int(req.GET.get('start', 0))
    end_time = int(req.GET.get('end', to_timestamp(datetime.now())))
    start_time = int(req.GET.get('start', 0))
    end_time = int(req.GET.get('end', to_timestamp(datetime.now())))
    
    messages = Message.objects.filter(conversation=convo)
    ret = []
    for message in messages:
        t: datetime = message.timestamp
        if to_timestamp(t) >= start_time and to_timestamp(t) <= end_time:
            if sender:
                if message.sender.username == sender:
                    ret.append(message)
            else:
                ret.append(message)
    
    ret = [format_message(m) for m in ret]
    return JsonResponse({'messages': ret, 'code': 0, 'info': 'Success'}, status=200)

def detailed_info(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    messageid = int(req.GET.get('message_id'))
    message = Message.objects.get(id=messageid)
    ret = {'readBy': [user.username for user in message.already_read.all()], 
            'responseCount': message.response_count}
    return request_success(ret)

def read_message(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    data = json.loads(req.body)
    username = data.get('username')
    convoid = data.get('conversationId')
    convo = Conversation.objects.get(id=convoid)
    messages = Message.objects.filter(conversation=convo)
    for m in messages:
        m.already_read.add(User.objects.get(username=username))
        m.save()
    return JsonResponse({'code': 0, 'info': 'Success'}, status=200)


@require_http_methods(["POST"])
def join_conversation(request: HttpRequest, conversation_id: int) -> HttpResponse:
    data = json.loads(request.body)
    username = data.get('username')

    # 验证 conversation_id 和 username 的合法性
    try:
        conversation = Conversation.objects.prefetch_related('members').get(id=conversation_id) 
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Invalid conversation ID'}, status=404)

    if conversation.type == 'private_chat':
        return JsonResponse({'error': 'Unable to join private chat'}, status=403)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid username'}, status=404)
    
    conversation.members.add(user)

    return JsonResponse({'result': 'success'}, status=200)

@require_http_methods(["POST"])
def leave_conversation(request: HttpRequest, conversation_id: int) -> HttpResponse:
    data = json.loads(request.body)
    username = data.get('username')

    # 验证 conversation_id 和 username 的合法性
    try:
        conversation = Conversation.objects.prefetch_related('members').get(id=conversation_id) 
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Invalid conversation ID'}, status=404)

    if conversation.type == 'private_chat':
        return JsonResponse({'error': 'Unable to leave private chat'}, status=403)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid username'}, status=404)
    
    conversation.members.remove(user)

    return JsonResponse({'result': 'success'}, status=200)
    
def to_timestamp(dt: datetime) -> int:
    # 转换为毫秒级 UNIX 时间戳
    return int(dt.timestamp() * 1_000)

def format_message(message: Message) -> dict:
    ret = {
        'id': message.id,
        'conversation': message.conversation.id,
        'sender': message.sender.username,
        # 'receivers': [user.username for user in message.receivers.all()],
        'content': message.content,
        'timestamp': to_timestamp(message.timestamp),
        # 'reply_to_id': message.reply_to_id,
        'responseCount': message.response_count,
        # 'isRead': bool(len(message.already_read) == 2),
        'readBy': [user.username for user in message.already_read.all()],
        'avatar': message.sender.avatar,
        # 'conversationType': message.conversation.type,
    }
    if message.reply_to_id:
        ret['reply_to'] = message.reply_to_id
    return ret

def format_conversation(conversation: Conversation) -> dict:
    return {
        'id': conversation.id,
        'type': conversation.type,
        'members': [user.username for user in conversation.members.all()],
    }
