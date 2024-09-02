import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models

class UserType(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    student = 'student', 'Student'
  
class CustomUserManager(UserManager):
    def _create_user(self, email, first_name, last_name, user_type, password, **extra_fields):
        if not email:
            raise ValueError("You have not provided a valid e-mail address")
        
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email=None, first_name=None, last_name=None, user_type=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, first_name, last_name, user_type, password, **extra_fields)
    
    def create_superuser(self, email=None, first_name=None, last_name=None, user_type=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, first_name, last_name, user_type, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, blank=False)
    first_name = models.CharField(max_length=255, blank=True, null=True, default='')
    last_name = models.CharField(max_length=255, blank=True, null=True, default='')
    user_type = models.CharField(max_length=50, choices=UserType.choices)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']
