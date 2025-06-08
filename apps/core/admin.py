from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile
from apps.parser.models import ContentSource, ParsedContent


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'interests', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'interests')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'interests'),
        }),
    )

admin.site.register(User, CustomUserAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_preferred_sources_display', 'get_reading_history_display')
    search_fields = ('user__username',)
    readonly_fields = ('preferred_sources', 'reading_history')

    def get_preferred_sources_display(self, obj):
        if obj.preferred_sources:
            sources = ContentSource.objects.filter(id__in=obj.preferred_sources, is_active=True)
            return ", ".join(source.name for source in sources)
        return "Нет источников"
    get_preferred_sources_display.short_description = 'Предпочитаемые источники'

    def get_reading_history_display(self, obj):
        if obj.reading_history:
            articles = ParsedContent.objects.filter(id__in=obj.reading_history).order_by('-parsed_at')[:5]
            return ", ".join(article.title for article in articles)
        return "Нет истории"
    get_reading_history_display.short_description = 'История чтения (5 последних)'

admin.site.register(UserProfile)