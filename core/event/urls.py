from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('vendor/', views.vendor, name='vendor'),
    path('vendor/upload-and-tag/', views.generate_tags_and_upload, name='upload_and_tag'),
    path("image_search/", views.image_search, name="image_search"),
    path("text-search/", views.text_search, name="text_search"),
    path("search-page/", lambda r: render(r, "event/search.html"), name="search_page"),
]
