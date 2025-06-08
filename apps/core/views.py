from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
import logging
from .models import UserProfile
from .forms import ProfileEditForm, CustomUserCreationForm
from apps.parser.models import ContentSource, ParsedContent
from django.http import JsonResponse


logger = logging.getLogger('core')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        logger.debug(f"Form data: {request.POST}")
        if form.is_valid():
            logger.info("Form is valid")
            user = form.save()
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('login')
        else:
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'core/dashboard.html', {'profile': profile})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    reading_history = ParsedContent.objects.filter(id__in=profile.reading_history).order_by('-parsed_at')[:10]
    preferred_sources = ContentSource.objects.filter(id__in=profile.preferred_sources, is_active=True)
    return render(request, 'profile/view.html', {
        'profile': profile,
        'reading_history': reading_history,
        'preferred_sources': preferred_sources
    })

@login_required
def profile_edit(request):
    current_interests = request.user.interests if hasattr(request.user, 'interests') and request.user.interests else []
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile_view')
    else:
        form = ProfileEditForm(instance=request.user, initial={
            'interests': ', '.join(current_interests) if current_interests else ''
        })
    
    content_sources = ContentSource.objects.filter(is_active=True)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    selected_sources = profile.preferred_sources

    return render(request, 'profile/edit.html', {
        'form': form,
        'current_interests': current_interests,
        'content_sources': content_sources,
        'selected_sources': selected_sources
    })


@login_required
def update_interests(request):
    if request.method == 'POST':
        interests = request.POST.get('interests', '')
        interests_list = [i.strip().lower() for i in interests.split(',') if i.strip()]
        
        request.user.interests = interests_list
        request.user.save()
        logger.info(f"Обновлены интересы пользователя {request.user.username}: {interests_list}")
        return JsonResponse({'status': 'success'})
    
    current_interests = request.user.interests if hasattr(request.user, 'interests') else []
    return render(request, 'profile/update_interests.html', {
        'current_interests': current_interests
    })