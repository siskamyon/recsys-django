from background_task import background
from .utils import parse_rss_feed
from .models import ContentSource
import logging


logger = logging.getLogger('parser')


@background(schedule=0)
def parse_rss_feeds(sources=None):
    """Парсинг RSS-лент для указанных источников или всех активных."""
    if sources:
        for source_data in sources:
            source = ContentSource(**source_data)
            logger.info(f"Парсинг источника: {source.name}")
            parse_rss_feed(source)
    else:
        sources = ContentSource.objects.filter(is_active=True)
        for source in sources:
            logger.info(f"Парсинг источника: {source.name}")
            parse_rss_feed(source)