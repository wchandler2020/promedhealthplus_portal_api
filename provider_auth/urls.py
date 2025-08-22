from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from provider_auth import views as api_views



urlpatterns = [
    path('provider/token/', api_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('provider/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('provider/register/', api_views.RegisterUser.as_view(), name='register'),
#    path('send-code/', api_views.SendVerificationCodeView.as_view(), name='send-code'),
    path('verify-code/', api_views.VerifyCodeView.as_view(), name='verify-code'),
    path('provider/profile/', api_views.ProviderProfileView.as_view(), name='provider-profile'),
    path('provider/contact-rep/', api_views.ContactRepView.as_view(), name='contact-rep'),
    
]
