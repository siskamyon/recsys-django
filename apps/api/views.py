from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.models import User, UserProfile
from apps.parser.models import ContentSource, ParsedContent
from apps.api.serializers import UserSerializer, ParsedContentSerializer, ContentSourceSerializer
from apps.parser.utils import parse_rss_feed
import logging


logger = logging.getLogger('api')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def content(self, request):
        user_interests = request.user.interests if hasattr(request.user, 'interests') else []
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        contents_query = ParsedContent.objects.select_related('source')
        
        if profile.preferred_sources:
            contents_query = contents_query.filter(source__id__in=profile.preferred_sources)

        if user_interests:
            contents_query = contents_query.filter(tags__overlap=user_interests)

        contents = contents_query.order_by('-published_at')
        
        page = self.paginate_queryset(contents)
        if page is not None:
            serializer = ParsedContentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ParsedContentSerializer(contents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def refresh_content(self, request):
        try:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            sources = ContentSource.objects.filter(is_active=True)
            if profile.preferred_sources:
                sources = sources.filter(id__in=profile.preferred_sources)

            for source in sources:
                parse_rss_feed(source)
                logger.info(f"Завершён парсинг источника: {source.name}")

            return Response({'status': 'success', 'message': 'Парсинг завершён'})
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {str(e)}")
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def add_to_history(self, request):
        article_id = request.data.get('article_id')
        if not article_id:
            return Response({'status': 'error', 'message': 'Укажите article_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            article = ParsedContent.objects.get(id=article_id)
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if article.id not in profile.reading_history:
                profile.reading_history.insert(0, article.id)
                if len(profile.reading_history) > 50:
                    profile.reading_history = profile.reading_history[:50]
                profile.save()
            return Response({'status': 'success', 'message': 'Добавлено в историю'})
        except ParsedContent.DoesNotExist:
            return Response({'status': 'error', 'message': 'Статья не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Ошибка при добавлении в историю: {str(e)}")
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def set_preferred_sources(self, request):
        source_ids = request.data.get('source_ids', [])
        if not isinstance(source_ids, list):
            return Response({'status': 'error', 'message': 'source_ids должен быть списком'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            valid_sources = ContentSource.objects.filter(id__in=source_ids, is_active=True).values_list('id', flat=True)
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.preferred_sources = list(valid_sources)
            profile.save()
            return Response({'status': 'success', 'message': 'Источники обновлены', 'sources': profile.preferred_sources})
        except Exception as e:
            logger.error(f"Ошибка при обновлении источников: {str(e)}")
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContentSourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentSource.objects.filter(is_active=True)
    serializer_class = ContentSourceSerializer