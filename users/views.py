import os

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError


# ---------------------------------------------------------------------------
# Cookie config — path must be set so delete_cookie matches set_cookie exactly
# ---------------------------------------------------------------------------
COOKIE_CONFIG = {
    "key": "refresh_token",
    "httponly": True,
    "secure": not settings.DEBUG,       # True in production (HTTPS only)
    "samesite": "Lax",
    "path": "/",                        # FIX 6: path needed for consistent delete
    "max_age": 14 * 24 * 60 * 60,      # 14 days — matches REFRESH_TOKEN_LIFETIME
}


def set_refresh_cookie(response, refresh_token_str):
    """Set the refresh token HttpOnly cookie consistently."""
    response.set_cookie(value=str(refresh_token_str), **COOKIE_CONFIG)


def delete_refresh_cookie(response):
    """
    FIX 6: Delete the cookie with the exact same attributes it was set with.
    Mismatched samesite/secure/path causes some browsers to silently ignore
    the deletion.
    """
    response.delete_cookie(
        "refresh_token",
        path=COOKIE_CONFIG["path"],
        samesite=COOKIE_CONFIG["samesite"],
    )


# ---------------------------------------------------------------------------
# Register / Delete account
# ---------------------------------------------------------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        email = request.data.get("email", "").strip()

        if not username or not password:
            return Response({"error": "Missing credentials"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        if email and User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=400)

        # Validate password against Django's validators before creating the user
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"error": e.messages}, status=400)

        # FIX 7: No bare except — let specific errors surface cleanly
        user = User.objects.create_user(username=username, password=password, email=email)
        refresh = RefreshToken.for_user(user)

        response = Response({
            "user": {"user_id": user.id, "username": user.username},
            "access": str(refresh.access_token),
        }, status=201)
        set_refresh_cookie(response, refresh)
        return response

    # FIX 1: Delete account must require authentication
    def delete(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        # Soft-delete: deactivate instead of hard delete to preserve referential integrity
        request.user.is_active = False
        request.user.save()

        # Also blacklist all outstanding tokens for this user
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        response = Response(status=204)
        delete_refresh_cookie(response)
        return response

    # FIX 1 (continued): Override get_permissions so DELETE requires auth
    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated()]
        return [AllowAny()]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response({"error": "Missing credentials"}, status=400)

        user = authenticate(username=username, password=password)

        if not user:
            # Same message for both "user not found" and "wrong password"
            # to avoid username enumeration
            return Response({"error": "Invalid credentials"}, status=401)

        if not user.is_active:
            return Response({"error": "Account is disabled"}, status=403)

        refresh = RefreshToken.for_user(user)

        response = Response({
            "user": {"user_id": user.id, "username": user.username},
            "access": str(refresh.access_token),
        }, status=200)
        set_refresh_cookie(response, refresh)
        return response


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        # FIX 4: Blacklist the token server-side so it can't be reused
        # even if someone captured it before logout
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                # Already expired or invalid — that's fine, just clear the cookie
                pass

        response = Response({"message": "Logged out"}, status=200)
        delete_refresh_cookie(response)
        return response


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------
class CustomTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"error": "No refresh token"}, status=401)

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"error": "Invalid or expired refresh token"}, status=401)

        data = serializer.validated_data  # "access", and "refresh" if ROTATE_REFRESH_TOKENS=True

        response = Response({"access": data["access"]}, status=200)

        # FIX 4 (continued): If ROTATE_REFRESH_TOKENS=True, push the new token into the cookie
        if "refresh" in data:
            set_refresh_cookie(response, data["refresh"])

        return response


# ---------------------------------------------------------------------------
# Password reset — request
# ---------------------------------------------------------------------------
class RequestPasswordReset(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"error": "Email is required"}, status=400)

        user = User.objects.filter(email=email).first()
        if user and user.is_active:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # FIX 2: Read frontend URL from env — never hardcode localhost
            frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
            reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"

            # TODO: replace print() with your email backend (e.g. django.core.mail.send_mail)
            # In production: send_mail("Reset your password", reset_link, settings.DEFAULT_FROM_EMAIL, [email])
            print(f"[DEBUG] Reset link: {reset_link}")

        # Always return the same response to prevent email enumeration
        return Response(
            {"message": "If an account exists, a reset link has been sent."},
            status=200,
        )


# ---------------------------------------------------------------------------
# Password reset — confirm
# ---------------------------------------------------------------------------
class PasswordResetConfirm(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get("uid", "")
        token = request.data.get("token", "")
        new_password = request.data.get("new_password", "")

        if not uidb64 or not token or not new_password:
            return Response({"error": "Missing fields"}, status=400)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid link"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        # FIX 3: Validate the new password before accepting it
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"error": e.messages}, status=400)

        user.set_password(new_password)
        user.save()

        # Blacklist all existing tokens so old sessions can't persist after a reset
        tokens = OutstandingToken.objects.filter(user=user)
        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)

        return Response({"message": "Password reset successful"}, status=200)


# ---------------------------------------------------------------------------
# Change password (authenticated)
# ---------------------------------------------------------------------------
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")

        if not old_password or not new_password:
            return Response({"error": "Missing fields"}, status=400)

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=400)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"error": e.messages}, status=400)

        user.set_password(new_password)
        user.save()

        # FIX 5: Blacklist all existing refresh tokens after password change
        # so other active sessions (e.g. another device) are forced to re-login
        tokens = OutstandingToken.objects.filter(user=user)
        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)

        # Issue fresh tokens for the current session
        refresh = RefreshToken.for_user(user)
        response = Response({
            "message": "Password updated successfully",
            "access": str(refresh.access_token),
        }, status=200)
        set_refresh_cookie(response, refresh)
        return response
