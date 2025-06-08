from django.db import models
from django.contrib.postgres.fields import ArrayField


class ContentSource(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    parser_type = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class ParsedContent(models.Model):
    source = models.ForeignKey(ContentSource, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.URLField()
    summary = models.TextField()
    content = models.TextField()
    published_at = models.DateTimeField()
    categories = models.JSONField(default=list)
    tags = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    parsed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-published_at']
    
    def __str__(self):
        return self.title