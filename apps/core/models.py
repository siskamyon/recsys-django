from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    nickname = models.CharField('Имя', max_length=150, blank=True)
    interests = models.JSONField('Интересы', default=list)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="user",
    )
    
    class Meta:
        db_table = 'user'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_sources = models.JSONField(default=list)
    reading_history = models.JSONField(default=list)
    
    def __str__(self):
        return f"{self.user.username}'s profile"