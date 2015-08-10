from rest_framework.views import APIView
from rest_framework.response import Response


from .utils import absolute_reverse
from api.users.serializers import UserSerializer


class Root(APIView):
    action = ''
    def get(self, request, format=None):
        if request.user and not request.user.is_anonymous():
            user = request.user
            current_user = UserSerializer(user, context={'request': request}).data
        else:
            current_user = None
        return Response({
            'meta': {
                'message': 'Welcome to the OSF API.',
                'version': request.version,
                'current_user': current_user,
            },
            'links': {
                'nodes': absolute_reverse('nodes:node-list'),
                'users': absolute_reverse('users:user-list'),
            }
        })


