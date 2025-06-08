from django.core.management.base import BaseCommand
from apps.parser.models import ContentSource


SOURCES = [
    {
        'name': 'Habr',
        'url': 'https://habr.com/ru/rss/articles/',
        'parser_type': 'rss'
    },
    {
        'name': 'Habr лучшее за неделю',
        'url': 'https://habr.com/ru/rss/articles/top/',
        'parser_type': 'rss'
    },
]


class Command(BaseCommand):
    help = 'Initialize news sources'

    def handle(self, *args, **options):
        for source in SOURCES:
            ContentSource.objects.get_or_create(
                url=source['url'],
                defaults={
                    'name': source['name'],
                    'parser_type': source['parser_type'],
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS('Successfully initialized sources'))