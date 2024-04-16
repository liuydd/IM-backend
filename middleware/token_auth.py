from django.http import JsonResponse
from utils.utils_jwt import check_jwt_token

class TokenAuthMiddleware:
    
    auth_urls = [
        '/modify',
        '/delete_user',

    ]

    auth_url_prefixes = [
        '/friend',
        '/friends',
        '/group',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.path in self.auth_urls or any([request.path.startswith(item) for item in self.auth_url_prefixes]):
            token = request.headers.get('Authorization')
            data = check_jwt_token(token)
            if data is None or 'username' not in data:
                return JsonResponse({'status_code': 401, 'info': 'Invalid token'})
            request.username = data['username']

        return self.get_response(request)