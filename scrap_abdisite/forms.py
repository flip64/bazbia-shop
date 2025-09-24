from django import forms
from .models import WatchedURL

class WatchedURLForm(forms.ModelForm):
    class Meta:
        model = WatchedURL
        fields = ['variant', 'supplier', 'url']
        widgets = {
            'variant': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'آدرس لینک محصول'}),
        }
        labels = {
            'variant': 'محصول',
            'supplier': 'تأمین‌کننده',
            'url': 'لینک محصول',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(WatchedURLForm, self).__init__(*args, **kwargs)

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if not self.user:
            raise forms.ValidationError("کاربر مشخص نشده است.")
        if WatchedURL.objects.filter(user=self.user, url=url).exists():
            raise forms.ValidationError("این لینک قبلاً توسط شما ثبت شده است.")
        return url

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user  # اتصال رکورد به کاربر فعلی
        if commit:
            instance.save()
        return instance



