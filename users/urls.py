from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    RequestPasswordReset,
    PasswordResetConfirm,
    ChangePasswordView,
)

urlpatterns = [
    # ✅ No "user/" prefix here — the main urls.py already adds it
    path('auth/account/', RegisterView.as_view(), name='account'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/password/reset/', RequestPasswordReset.as_view(), name='password_reset'),
    path('auth/password/reset/confirm/', PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('auth/password/change/', ChangePasswordView.as_view(), name='password_change'),
]