import feedparser
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import ParsedContent
import re
import logging
import requests
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO


logger = logging.getLogger('parser')


def clean_html(text):
    """Удаление HTML-тегов и лишних пробелов из текста."""
    if not isinstance(text, str) or not text.strip():
        logger.debug(f"Пустой или некорректный текст для очистки: {text!r}")
        return ""
    try:
        soup = BeautifulSoup(text, 'html.parser')
        cleaned_text = soup.get_text()
        return re.sub(r'\s+', ' ', cleaned_text).strip()
    except Exception as e:
        logger.error(f"Ошибка очистки HTML: {str(e)}")
        return ""


def parse_rss_feed(source):
    """Парсинг RSS-ленты для заданного ContentSource и сохранение в ParsedContent."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(source.url, headers=headers, timeout=10)
        response.raise_for_status()
        
        content = response.text
        encoding = response.encoding or 'utf-8'
        logger.debug(f"Кодировка ленты {source.name}: {encoding}")
        
        try:
            ET.parse(StringIO(content))
        except ET.ParseError as xml_error:
            logger.warning(f"Невалидный XML в {source.name}: {xml_error}. Первые 500 символов: {content[:500]!r}")
            content = re.sub(r'[^\x00-\x7F]+', '', content)
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        feed = feedparser.parse(BytesIO(content.encode(encoding)))
        if feed.bozo:
            logger.error(f"Ошибка парсинга {source.name}: {feed.bozo_exception}")
            return
        
        for entry in feed.entries[:20]:
            if ParsedContent.objects.filter(url=entry.link).exists():
                logger.debug(f"Пропущен дубликат: {entry.link}")
                continue
            
            title = clean_html(entry.get('title', 'Без заголовка'))
            if not title:
                logger.debug(f"Пропущена запись без заголовка: {entry.link}")
                continue
            
            summary = clean_html(entry.get('summary', entry.get('description', '')))
            content = clean_html(entry.get('content', [{}])[0].get('value', summary))
            
            published_at = entry.get('published_parsed') or entry.get('updated_parsed')
            published_at = timezone.make_aware(timezone.datetime(*published_at[:6])) if published_at else timezone.now()
            
            categories = [clean_html(tag.get('term', '')).lower() for tag in entry.get('tags', []) if tag.get('term', '')]
            tags = categories
            
            ParsedContent.objects.create(
                source=source,
                title=title[:255],
                url=entry.link,
                summary=summary,
                content=content,
                published_at=published_at,
                categories=categories,
                tags=tags
            )
            logger.info(f"Сохранена запись: {title}")
    except requests.RequestException as e:
        logger.error(f"Ошибка HTTP-запроса к {source.url}: {str(e)}")
    except Exception as e:
        logger.error(f"Общая ошибка обработки {source.name}: {str(e)}", exc_info=True)