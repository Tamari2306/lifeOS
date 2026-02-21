from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/',      admin.site.urls),
    path('accounts/',   include('users.urls')),
    path('fitness/',    include('fitness.urls')),
    path('hydration/',  include('hydration.urls')),
    path('finance/',    include('finance.urls')),
    path('bible/',      include('bible.urls')),
    path('checklist/',  include('checklist.urls')),
    path('meals/',      include('meals.urls')),
    path('',            include('fitness.urls')),
]