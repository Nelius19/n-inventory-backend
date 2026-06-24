from rest_framework.response import Response
from rest_framework.decorators import api_view
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
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import EmailMultiAlternatives

User = get_user_model() # Using custom auth User model

# Create your views here.

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
    user = serializer.validated_data["user"]
    login(request, user)

    return Response(UserSerializer(user).data, status=200)
                            
    # user = serializer.validated_data["user"]            # Store returned user object (validated data)
    # if user:  
    #     login(request, user)                            # Set sessionId, cookie
    #     return Response(UserSerializer(user).data, status=200) # Converts User object to Json format using serializer
    
    # return Response ({"error": "Wrong username or password"}, status=401)


# VERIFY AUTHENTICATION OF 'USER SESSION ID' FROM BROWSER COOKIE (authentication done in background)
@api_view(['GET'])
def user_session(request):
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=200)
    return Response({"user": None}, status=401)


# LOGOUT USER
@api_view(['POST'])
def logout_user(request):
    logout(request) # Clears authenticated user session
    return Response({"success:", True})


# REQUEST PASSWORD RESET
@api_view(['POST'])
def password_reset_request(request):
    # Pass request data to Serializer
    serializer = PasswordResetRequestSerializer(data = request.data)

    # Check if data satisfy all validation constraints (serializer), return error otherwise
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    user = serializer.validated_data.get("user")            # Store returned user object (validated data)
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))   # User Id requesting password reset
        token = default_token_generator.make_token(user)    # Token creation: timestamp and hash signature (id, password, timestamp, secret key)
        
        # reset_link = f"http://localhost:5173/password-reset/{uid}/{token}/"
        reset_link = f"{settings.FRONTEND_URL}/password-reset/{uid}/{token}/"
        subject = "Password Reset - N-Inventory"

        text_content = f"""
        Click here to reset your password:
        {reset_link}
        """

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

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        email.attach_alternative(html_content, "text/html")
        try:
            email.send()
        except Exception as e:
            print(f"Email error: {e}")
                
    return Response({"message":"If the email exists, a reset link has been sent"}, status=200)


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
    # new_password = request.data.get('new_password')

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

    # if new_password:
    #     user.set_password(new_password)

    # user.save()

    # if new_password:
    #     update_session_auth_hash(request, user)
    #     return Response({"password_success": "Password updated successfully"})
    
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
