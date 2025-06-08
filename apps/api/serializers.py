from rest_framework import serializers
from apps.core.models import User, UserProfile
from apps.parser.models import ContentSource, ParsedContent

class ContentSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSource
        fields = ['id', 'name', 'url', 'parser_type', 'is_active']

class ParsedContentSerializer(serializers.ModelSerializer):
    source = ContentSourceSerializer(read_only=True)

    class Meta:
        model = ParsedContent
        fields = ['id', 'source', 'title', 'url', 'summary', 'content', 'published_at', 'categories', 'tags', 'parsed_at']

class UserProfileSerializer(serializers.ModelSerializer):
    preferred_sources = serializers.ListField(child=serializers.IntegerField(), required=False)
    reading_history = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['preferred_sources', 'reading_history']

    def get_reading_history(self, obj):
        articles = ParsedContent.objects.filter(id__in=obj.reading_history).order_by('-parsed_at')[:10]
        return ParsedContentSerializer(articles, many=True).data

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    interests = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'email', 'interests', 'profile']
        read_only_fields = ['id', 'username']

    def validate_interests(self, value):
        return [interest.lower() for interest in value if interest.strip()]

    def update(self, instance, validated_data):
        interests = validated_data.pop('interests', None)
        if interests is not None:
            instance.interests = interests
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance