from django.urls import path

from . import views

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('signup/', views.SignUpUserView.as_view(), name="sign-up"),
    path('login/', views.CustomTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', views.CustomTokenVerifyView.as_view(), name='token_verify'),
    path('activate/<uidb64>/<token>/',
         views.ActivateUserView.as_view(), name='activate'),
]
