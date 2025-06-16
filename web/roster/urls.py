from django.urls import path
from web.roster.views import roster_view

app_name = 'roster'

urlpatterns = [
    path('', roster_view, name='index'),
] 