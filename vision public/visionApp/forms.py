from django import forms
from .models import Message, ChatbotConfiguration

class MessageForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 1, 'cols': 80, 'placeholder': 'type type type'}))
    class Meta:
        model = Message
        fields = ['text']

class ChatbotPersonalityForm(forms.ModelForm):
    class Meta:
        model = ChatbotConfiguration
        fields = ['personality']
