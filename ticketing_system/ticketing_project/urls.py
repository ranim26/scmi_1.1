from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='tickets/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('tickets.urls')),
    # PWA URLs
    path('', include('pwa.urls')),
    path('serviceworker.js', TemplateView.as_view(template_name='serviceworker.js', content_type='application/javascript'), name='serviceworker'),
    # Suppress Chrome DevTools well-known 404
    path('.well-known/appspecific/com.chrome.devtools.json', lambda request: JsonResponse({}, safe=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
