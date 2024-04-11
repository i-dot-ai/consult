import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import validate_email
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_staff=False):
        # If there's no pw, assign a long random one that won't be used
        if password is None:
            password = str(uuid.uuid4())

        user = self.model(
            email=self.normalize_email(email).lower(),
            is_staff=is_staff,
        )

        user.set_password(password)
        user.full_clean()

        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    # boilerplate required by django admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
