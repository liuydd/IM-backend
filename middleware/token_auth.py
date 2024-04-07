from board.models import User
from django.http import JsonResponse
from utils.utils_jwt import check_jwt_token

class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        token = request.headers.get('Authorization')
        
        if token:
            data = check_jwt_token(token)
            try:
                user = User.objects.get(username=data['username'])
                request.user = user
            except:
                return JsonResponse({'status_code': 401, 'info': 'Invalid token'})
        
        return self.get_response(request)