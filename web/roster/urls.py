from django.urls import path
from web.roster.views import roster_view, character_detail_view, update_character_field

app_name = 'roster'

urlpatterns = [
    path('', roster_view, name='index'),
    path('detail/<str:char_name>/<int:char_id>/', character_detail_view, name='character_detail'),
    path('detail/<str:char_name>/<int:char_id>/update/', update_character_field, name='update_character_field'),
] 