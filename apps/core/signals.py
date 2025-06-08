from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from .models import User, UserProfile
from apps.parser.models import ContentSource
from apps.parser.tasks import parse_rss_feeds
import logging


logger = logging.getLogger('parser')

signal_enabled = True


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создаём профиль с дефолтными источниками при создании пользователя."""
    if created:
        default_sources = list(ContentSource.objects.filter(
            is_active=True
        ).values_list('id', flat=True)[:3])
        UserProfile.objects.create(
            user=instance,
            preferred_sources=default_sources
        )
        logger.info(f"Создан профиль для {instance.username} с источниками: {default_sources}")


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """Обработчик создания/обновления пользователя."""
    global signal_enabled
    if not signal_enabled:
        return
    
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    
    if not hasattr(instance, 'interests') or instance.interests is None:
        instance.interests = []
    else:
        new_interests = [interest.lower() for interest in instance.interests]
        if new_interests != instance.interests:
            instance.interests = new_interests
            signal_enabled = False
            try:
                instance.save(update_fields=['interests'])
            finally:
                signal_enabled = True
    
    if not created:
        profile.save()
        logger.info(f"Обновлён профиль для {instance.username}")
    
    update_fields = kwargs.get('update_fields') or set()
    if created or 'interests' in update_fields or 'preferred_sources' in update_fields:
        trigger_personalized_parsing(instance)


@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """Обработчик входа пользователя с кэшированием."""
    cache_key = f"user_{user.id}_last_parse"
    if not cache.get(cache_key):
        trigger_personalized_parsing(user)
        cache.set(cache_key, True, timeout=7200)  # Кэш на 2 часа
        logger.info(f"Запущен парсинг при входе для {user.username}")


def trigger_personalized_parsing(user):
    """Запуск персонализированного парсинга с проверками."""
    try:
        if not hasattr(user, 'userprofile'):
            logger.warning(f"Нет профиля у {user.username}")
            return

        if not user.userprofile.preferred_sources:
            logger.info(f"Нет preferred_sources у {user.username}, парсинг всех активных источников")
            parse_rss_feeds()
            return

        sources = ContentSource.objects.filter(
            id__in=user.userprofile.preferred_sources,
            is_active=True
        )
        if not sources:
            logger.info(f"Нет активных preferred_sources у {user.username}")
            return

        parse_rss_feeds(sources=list(sources.values('id', 'url', 'name', 'parser_type', 'is_active')))
        logger.info(f"Запущен парсинг для {user.username} с источниками: {[s.name for s in sources]}")

    except Exception as e:
        logger.error(f"Ошибка парсинга для {user.username}: {str(e)}", exc_info=True)