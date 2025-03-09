from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import UserProfile

class PhoneNumberBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Treat 'username' as the phone number
        try:
            user_profile = UserProfile.objects.get(phone_number=username)
            user = user_profile.user
            if user.check_password(password):
                return user
        except UserProfile.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None