from django.contrib import admin
from django.urls import include, path
from quiz_system.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('quiz/', include('quiz.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Django's built-in auth URLs
]
