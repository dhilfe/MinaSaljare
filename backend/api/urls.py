from django.urls import path

from .views import health, login, me, team


urlpatterns = [
    path('health/', health, name='health'),
    path('v1/auth/login/', login, name='login'),
    path('v1/me/', me, name='me'),
    path('v1/team/', team, name='team'),
]
