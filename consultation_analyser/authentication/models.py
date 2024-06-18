import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_staff=False, idempotent=False):
        # If there's no pw, assign a long random one that won't be used
        if password is None:
            password = str(uuid.uuid4())

        try:
            user = self.model(
                email=self.normalize_email(email).lower(),
                is_staff=is_staff,
            )

            user.set_password(password)
            user.full_clean()

        except ValidationError as e:
            # only swallow exception if this is an email conflict and we've chosen to ignore it
            if idempotent and (["User with this Email address already exists."] == e.messages):
                return user
            else:
                raise e

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

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
