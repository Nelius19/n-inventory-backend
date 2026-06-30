from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from accounts.serializers import UserSerializer, RegisterSerializer, LoginSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer
from house.services import create_house_for
from house.serializers import HouseSerializer
from django.contrib.auth import update_session_auth_hash
from rest_framework.permissions import IsAuthenticated
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from rest_framework import status
import requests

from rest_framework.permissions import AllowAny

User = get_user_model() # Using custom auth User model

# Create your views here.

#
@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})


# CREATE NEW USER
@api_view(['POST'])
def register_user(request):
    # Pass request data from vue(frontend) to RegisterSerializer, and create an instance [serializer]
    serializer = RegisterSerializer(data = request.data)

    # Model level validation (is_valid method check if data satisfy model and serializer contraints)
    if serializer.is_valid():
        user = serializer.save()                # Create new user if none exists
        login(request, user)                    # Set sessionId in cookie
        
        house = create_house_for(user)          ##### Pass user object, and store returned house object

        # Serialized python object to python dict and then to json format
        userData = UserSerializer(user).data    
        houseData = HouseSerializer(house).data
        return Response({"user": userData, "house": houseData}, status=200)
    return Response(serializer.errors, status=400)


# LOGIN EXISTING USER
@api_view(['POST'])
def login_user(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})   # Passed request data to Serializer
  
    serializer.is_valid(raise_exception=True) # Check if data satisfy all validation constraints (serializer), return error if not
    user = serializer.validated_data["user"]                # Store returned user object (validated data)
    login(request, user)                                    # Set sessionId, cookie

    return Response(UserSerializer(user).data, status=200)  # Converts User object to Json format using serializer
                            

# VERIFY AUTHENTICATION OF 'USER SESSION ID' FROM BROWSER COOKIE (authentication done in background)
@api_view(['GET'])
@permission_classes([AllowAny])  # Ensure anyone can access the initial check
def user_session(request):
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=200)
    return Response({"user": None, "isAuthenticated": False}, status=200)


# LOGOUT USER
@api_view(['POST']) # Must be POST!
@permission_classes([IsAuthenticated])
def logout_user(request):
    logout(request) # This flushes the sessionid cookie cleanly
    return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


# Reset password
@api_view(['POST'])
def password_reset_request(request):

    serializer = PasswordResetRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    user = serializer.validated_data.get("user")
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = (f"{settings.FRONTEND_URL}/password-reset/{uid}/{token}/")

        subject = "Password Reset - N-Inventory"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
            <div style="max-width:520px; margin:auto; background:white; padding:25px; border-radius:10px;">

                <h2 style="color:#2563eb;">Password Reset Request</h2>

                <p>You requested to reset your password for <b>N-Inventory</b>.</p>

                <p style="margin:30px 0;">
                    <a href="{reset_link}"
                    style="
                        background:#2563eb;
                        color:white;
                        padding:12px 22px;
                        text-decoration:none;
                        border-radius:6px;
                        font-weight:bold;
                        display:inline-block;">
                    Reset Password
                    </a>
                </p>

                <p style="font-size:12px; color:gray;">
                    If you did not request this, you can ignore this email.
                </p>

            </div>
        </body>
        </html>
        """

        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": settings.BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json={
                    "sender": {
                        "name": "N-Inventory",
                        "email": "cmulbahpl@gmail.com",  # verified Brevo sender
                    },
                    "to": [{"email": user.email,}],
                    "subject": subject,
                    "htmlContent": html_content,
                },
                timeout=15,
            )
            response.raise_for_status()

            return Response(
                {
                    "success": True,
                    "message": "Password reset email sent",
                    "brevo_status": response.status_code,
                },
                status=200,
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": str(e),
                    "type": e.__class__.__name__,
                },
                status=500,
            )

    return Response({"message": "If the email exists, a reset link has been sent" }, status=200)


# RESET USER PASSWORD
@api_view(['POST'])
def set_new_password(request):
    # Pass data to serializer
    serializer = SetNewPasswordSerializer(data = request.data)

    # Check if data is valid against contraints
    if not serializer.is_valid():
        return Response(serializer.errors, status=401)
    
    # Store validated user data
    user = serializer.validated_data['user']
    password = serializer.validated_data['password']

    # Save user new password
    user.set_password(password)
    user.save()

    return Response('Password reset successful!!', status=200)


#
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user(request):
   
    user = request.user

    username = request.data.get('username')
    email = request.data.get('email')
    current_password = request.data.get('current_password')

    # Verify and authenticate user data
    if not user.check_password(current_password):
        return Response({"error": "Your password is incorrect"}, status=400)
    
    if username and User.objects.filter(username=username).exclude(pk=user.pk).exists():
        return Response({"error": "Username already exists"}, status=400)
    
    if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
        return Response({"error": "Email already exists"}, status=400)
    
    # Set new data
    if username:
        user.username = username
      
    if email:
        user.email = email

    user.save()
    
    return Response({"message": "Updated successfully"})


#
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_password(request):
      
    user = request.user

    new_password = request.data.get('new_password')
    current_password = request.data.get('current_password')

    # check if user password match
    if not user.check_password(current_password):
        return Response({"error": "Current password is incorrect"}, status=400)
    
    if user.check_password(new_password):
        return Response({"error": "New password must be different from the current password"}, status=400)
    
    # if match and new password is available, update password and sessess auth
    if new_password:
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response({"password_success": "Password updated successfully"})
    return Response({"error" : "Insert new password"}, status=400)
