from django.contrib import admin
from apps.parser.models import ContentSource, ParsedContent


@admin.register(ContentSource)
class ContentSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'parser_type', 'is_active')
    list_editable = ('is_active',)


@admin.register(ParsedContent)
class ParsedContentAdmin(admin.ModelAdmin):
    list_display = ('source', 'title', 'url', 'summary', 'content',
                    'published_at', 'categories', 'tags', 'parsed_at')