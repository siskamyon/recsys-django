from django.urls import path
from . import views


urlpatterns = [
    path('content', views.ContentListView.as_view(), name='content_list'),
    path('content/refresh/', views.RefreshContentView.as_view(), name='content_refresh'),
    path('article/<int:article_id>/', views.ArticleView.as_view(), name='view_article'),
]