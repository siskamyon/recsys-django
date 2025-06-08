from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from apps.parser.models import ContentSource

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ("username", "nickname", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    interests = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Введите интересы'
    )

    preferred_sources = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Введите ID предпочтительных источников через запятую (например: 1,2,3)'
    )

    class Meta:
        model = User
        fields = ['nickname', 'email', 'interests', 'preferred_sources']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'userprofile'):
            profile = self.instance.userprofile
            self.fields['preferred_sources'].initial = ','.join(map(str, profile.preferred_sources)) if profile.preferred_sources else ''

    def clean_interests(self):
        interests = self.cleaned_data.get('interests')
        if isinstance(interests, str):
            return [i.strip().lower() for i in interests.split(',') if i.strip()]
        return interests or []

    def clean_preferred_sources(self):
        preferred_sources = self.cleaned_data.get('preferred_sources')
        if not preferred_sources:
            return []
        try:
            source_ids = [int(s.strip()) for s in preferred_sources.split(',') if s.strip()]
            valid_sources = ContentSource.objects.filter(id__in=source_ids, is_active=True).values_list('id', flat=True)
            return list(valid_sources)
        except ValueError:
            raise forms.ValidationError("ID источников должны быть целыми числами")

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.preferred_sources = self.cleaned_data['preferred_sources']
            profile.save()
        return user