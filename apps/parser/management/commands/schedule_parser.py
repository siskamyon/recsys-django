from django.core.management.base import BaseCommand
from apps.parser.tasks import parse_rss_feeds


class Command(BaseCommand):
    help = 'Планирование задачи парсинга RSS-лент'

    def handle(self, *args, **options):
        parse_rss_feeds(repeat=30*60, queue='default')
        self.stdout.write(self.style.SUCCESS('Задача парсинга RSS-лент успешно запланирована'))