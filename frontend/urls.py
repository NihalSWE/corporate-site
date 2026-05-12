from django.urls import path
from .import views


urlpatterns = [
    path('',views.home,name='home'),
    path('aboutUs/',views.aboutUs,name='aboutUs'),
    path('contact/',views.contact,name='contact'),
    path('ourteam/',views.ourteam,name='ourteam'),
    path('ourteam/<int:member_id>/', views.team_member_detail_by_id, name='team_member_detail_by_id'),
    path('ourteam/<slug:member_slug>/', views.team_member_detail, name='team_member_detail'),
    path('gallery/video/', views.video_gallery, name='video_gallery'),
    path('gallery/photo/', views.photo_gallery, name='photo_gallery'),
    path('gallery/photo/<slug:slug>/', views.photo_gallery_detail, name='photo_gallery_detail'),
    path('sister-concern/<slug:slug>/', views.sister_concern_detail, name='sister_concern_detail'),
    
     
]
