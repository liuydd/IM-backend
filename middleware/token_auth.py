from django.http import JsonResponse
from utils.utils_jwt import check_jwt_token

class TokenAuthMiddleware:
    
    authUrl = ['modify', 'delete_user']
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.path in self.authUrl or request.path.startswith('friends' or 'friend'):
            token = request.headers.get('Authorization')
            data = check_jwt_token(token)
            print(data)
            try:
                tokenUser = data['username']
                requestUser = request.body['username']
                
                if tokenUser != requestUser:
                    return JsonResponse({'status_code': 401, 'info': 'Invalid token'})
                
            except:
                return JsonResponse({'status_code': 401, 'info': 'Invalid token'})
            
        return self.get_response(request)