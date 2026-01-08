from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Team

from .serializers import TeamSerializer


@api_view(['GET'])
def health(request):
	return Response({"status": "ok"})


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
	email = (request.data or {}).get('email')
	password = (request.data or {}).get('password')

	if not email or not password:
		return Response({'detail': 'email and password are required'}, status=400)

	user = authenticate(request, email=email, password=password)
	if user is None:
		return Response({'detail': 'Invalid credentials'}, status=401)
	if not user.is_active:
		return Response({'detail': 'User is inactive'}, status=403)

	refresh = RefreshToken.for_user(user)
	return Response(
		{
			'access_token': str(refresh.access_token),
			'user': {
				'id': str(user.id),
				'email': user.email,
				'role': user.role,
				'first_name': user.first_name,
				'last_name': user.last_name,
			},
		}
	)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
	user = request.user
	return Response(
		{
			'id': str(user.id),
			'email': user.email,
			'role': getattr(user, 'role', None),
			'first_name': user.first_name,
			'last_name': user.last_name,
			'children': [],
		}
	)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team(request):
	user = request.user

	if getattr(user, 'team_id', None):
		return Response(TeamSerializer(user.team).data)

	if getattr(user, 'role', None) == 'coach':
		team_obj = Team.objects.filter(coach=user).first()
		if team_obj:
			return Response(TeamSerializer(team_obj).data)

	return Response({'detail': 'No team associated with user'}, status=404)


