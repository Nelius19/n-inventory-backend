from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.validators import UniqueValidator

User = get_user_model() # Using custom auth User model

####### Validates againts [model] contraints (with ModelSerializer), expose valid data [fields] to user/frontend 
####### & Convert data to json format

# Validates user data against model fields contraints and expose user fields 
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


# Validates data against model contraints
class RegisterSerializer(serializers.ModelSerializer):

    # Overrides DRF's default unique validation messages
    username = serializers.CharField(
        validators=[ 
            UniqueValidator(
                queryset=User.objects.all(), 
                message="This username is not available"
            )
        ]
    )

    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email is not available"
            )
        ]
    )

    # Validate user data against model contraints and create new user
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {"password": {"write_only": True}}
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data) # Hashes password with (create_user) and unpack data to save using **


####### Not tied to Models, not exposing fields to user(s) (use .Serializer) #######

# Validate user login data against db contraints
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        # cleaned + field-validated data before (validated_data) is produced
        username = attrs.get("username")
        password = attrs.get("password")

        request = self.context.get('request')

        # Authenticate validated data (check if user exist & password matches), returns user object
        user = authenticate(request=request, username=username, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        
        attrs['user'] = user    # Attach user to attrs so the view does NOT need to query user again
        return attrs

# Validate user reset email against db contraints
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')        
        
        # Attach user to attrs so the view does NOT need to query user again
        attrs['user'] = User.objects.filter(email=email).first() 
        return attrs  


# Validate user reset data against db contraints
class SetNewPasswordSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    token = serializers.CharField(write_only = True)
    password = serializers.CharField(write_only = True)

    # Custom validation (data pass in attrs)
    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs.get("user_id")))             # Decode and convert userID to string
            user = User.objects.get(pk=uid)                                          # Get user object with uid
        except (User.DoesNotExist, OverflowError, TypeError, ValueError):
            raise serializers.ValidationError({"msg": "Invalid user"})
        
        valid_token = default_token_generator.check_token(user, attrs.get("token"))      # Check if token is valid against user object
        if not valid_token:
            raise serializers.ValidationError({"message": "Invalid token. Please request new password reset."})

        attrs["user"] = user    # Attach user to attrs so the view does NOT need to query user again
        
        return attrs
    