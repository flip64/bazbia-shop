from django import forms
from .models import WatchedURL

class WatchedURLForm(forms.ModelForm):
    class Meta:
        model = WatchedURL
        fields = ['url']
        widgets = {
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'آدرس لینک محصول'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(WatchedURLForm, self).__init__(*args, **kwargs)

    def clean_url(self):
        url = self.cleaned_data['url']
        if WatchedURL.objects.filter(user=self.user, url=url).exists():
            raise forms.ValidationError("این لینک قبلاً توسط شما ثبت شده است.")
        return url