from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .tasks import parse_rss_feeds
from .models import ContentSource, ParsedContent
from apps.core.models import UserProfile
import logging


logger = logging.getLogger('parser')


class ContentListView(LoginRequiredMixin, View):
    def get(self, request):
        user_interests = [interest.lower() for interest in (request.user.interests if hasattr(request.user, 'interests') else [])]
        
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        preferred_sources = profile.preferred_sources or []
        logger.debug(f"Preferred sources for user {request.user.username}: {preferred_sources}")

        contents_query = ParsedContent.objects.select_related('source')

        if preferred_sources:
            contents_query = contents_query.filter(source__id__in=preferred_sources)

        if user_interests:
            contents_query = contents_query.filter(tags__overlap=user_interests)

        contents = contents_query.order_by('-published_at')[:50]
        
        last_update = ParsedContent.objects.order_by('-parsed_at').first()
        last_update = last_update.parsed_at if last_update else None

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        content_ids = [content.id for content in contents]
        for content_id in content_ids:
            if content_id not in profile.reading_history:
                profile.reading_history.insert(0, content_id)
                if len(profile.reading_history) > 50:
                    profile.reading_history = profile.reading_history[:50]
        profile.save()
        
        context = {
            'contents': contents,
            'user_interests': user_interests,
            'last_update': last_update,
        }
        return render(request, 'parser/content_list.html', context)


class RefreshContentView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Неверный запрос'}, status=400)
        
        try:
            profile = getattr(request.user, 'userprofile', None)
            sources = ContentSource.objects.filter(is_active=True)
            if profile and profile.preferred_sources:
                sources = sources.filter(id__in=profile.preferred_sources)
            
            for source in sources:
                parse_rss_feeds(source)
                logger.info(f"Завершён парсинг источников: {sources}")
            
            user_interests = [interest.lower() for interest in (request.user.interests if hasattr(request.user, 'interests') else [])]
            if user_interests:
                contents = ParsedContent.objects.filter(
                    tags__overlap=user_interests
                ).select_related('source').order_by('-published_at')[:50]
            else:
                contents = ParsedContent.objects.select_related('source').order_by('-published_at')[:50]
            
            html = render(request, 'parser/content_partial.html', {'contents': contents}).content.decode('utf-8')
            return JsonResponse({
                'status': 'success',
                'message': 'Парсинг завершён',
                'html': html,
                'last_update': timezone.now().strftime('%d.%m.%Y %H:%M')
            })
        except Exception as e:
            logger.error(f"Ошибка при синхронном парсинге: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        

class ArticleView(LoginRequiredMixin, View):
    def get(self, request, article_id):
        article = get_object_or_404(ParsedContent, id=article_id)
        return render(request, 'parser/article.html', {'article': article})