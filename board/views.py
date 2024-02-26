import json
from django.http import HttpRequest, HttpResponse

from board.models import Board, User
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token


@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")


@CheckRequire
def login(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    
    username = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    # TODO Start: [Student] Finish the login function according to the comments below
    # If the user does not exist, create a new user and save; while if the user exists, check the password
    # If new user or checking success, return code 0, "Succeed", with {"token": generate_jwt_token(user_name)}
    # Else return request_failed with code 2, "Wrong password", http status code 401
    
    return request_failed(1, "Not implemented", 501)
    # TODO End: [Student] Finish the login function according to the comments above


def check_for_board_data(body):
    board = require(body, "board", "string", err_msg="Missing or error type of [board]")
    # TODO Start: [Student] add checks for type of boardName and userName
    board_name = ""
    user_name = ""
    # TODO End: [Student] add checks for type of boardName and userName
    
    assert 0 < len(board_name) <= 50, "Bad length of [boardName]"
    
    # TODO Start: [Student] add checks for length of userName and board
    
    # TODO End: [Student] add checks for length of userName and board
    
    
    # TODO Start: [Student] add more checks (you should read API docs carefully)
    
    # TODO End: [Student] add more checks (you should read API docs carefully)
    
    return board, board_name, user_name


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
        
        # Then invoke `check_for_board_data` to check the body data and get the board_state, board_name and user_name. Check the user_name with the username in jwt_token_payload. If not match, return code 3, "Permission denied", http status code 403
        
        # Find the corresponding user instance by user_name. We can assure that the user exists.
        
        # We lookup if the board with the same name and the same user exists.
        ## If not exists, new an instance of Board type, then save it to the database.
        ## If exists, change corresponding value of current `board`, then save it to the database.
        
        return request_failed(1, "Not implemented", 501)
        
        # TODO End: [Student] Finish the board view function according to the comments above
        
    else:
        return BAD_METHOD


@CheckRequire
def boards_index(req: HttpRequest, index: any):
    
    idx = require({"index": index}, "index", "int", err_msg="Bad param [id]", err_code=-1)
    assert idx >= 0, "Bad param [id]"
    
    if req.method == "GET":
        params = req.GET
        board = Board.objects.filter(id=idx).first()  # Return None if not exists
        
        if board:
            return request_success(
                return_field(board.serialize(), ["board", "boardName", "userName"])
            )
            
        else:
            return request_failed(1, "Board not found", status_code=404)
    
    elif req.method == "DELETE":
        # TODO Start: [Student] Finish the board_index view function
        return request_failed(1, "Not implemented", 501)
        # TODO End: [Student] Finish the board_index view function
    
    else:
        return BAD_METHOD


# TODO Start: [Student] Finish view function for user_board

# TODO End: [Student] Finish view function for user_board
