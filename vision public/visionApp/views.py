from .models import Message, ChatbotConfiguration, Character, Conversation
from .forms import MessageForm, ChatbotPersonalityForm
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
import openai
import json
import asyncio
import time

openai.api_key = 'sk-'

def new_bots(request):
    return render(request, 'visionApp/new_bots.html')

def index(request):
    return render(request, 'visionApp/index.html')

def chat_view(request, character):
    if request.method == 'POST':
        print("POST")
        # Handle any POST request logic here if necessary
    else:
        form = MessageForm()
        messages = Message.objects.all()
        context = {
            'form': form,
            'messages': messages,
            'initial_character': character  # Pass the character to the template
        }
        return render(request, 'visionApp/chat_view.html', context)

def purpose(request):
    return render(request, 'visionApp/purpose.html')

def delete_all_messages(request):
    if request.method == "POST":
        Message.objects.all().delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})

def settings(request):
    current_personality = None
    try:
        # Get the latest chatbot personality from the database
        chatbot_config = ChatbotConfiguration.objects.latest('id')
        current_personality = chatbot_config.personality
    except ChatbotConfiguration.DoesNotExist:
        current_personality = "You are a knowledgeable and concise assistant."

    if request.method == 'POST':
        form = ChatbotPersonalityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('settings')
    else:
        # If there's a current personality, initialize the form with it
        form = ChatbotPersonalityForm(initial={'personality': current_personality})

    # Pass the current personality to the template
    context = {
        'form': form,
        'current_personality': current_personality  # make sure this is passed here
    }
    return render(request, 'visionApp/settings.html', context)
