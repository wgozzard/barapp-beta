from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import openai
import os
import string
import logging
from dotenv import load_dotenv



load_dotenv()

api_key = os.getenv("OPENAI_KEY", None)

logger = logging.getLogger(__name__)

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=password)
            login(request, user)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Handle login form submission
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # Set session variable to indicate prompt has been displayed
                session_key = request.session.session_key
                if session_key:
                    session = Session.objects.get(session_key=session_key)
                    session['prompt_displayed'] = True
                    session.save()

                return redirect('home')  # Redirect to the home page after successful login
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form})


@login_required
def chatbot(request):
    chatbot_response = None
    api_key = os.environ.get("OPENAI_KEY")
    user_input = ''

    if api_key is not None and request.method == 'POST':
        openai.api_key = api_key
        user_input = request.POST.get('user_input')

        if user_input:
            # Determine the chatbot's area of expertise based on user input
            if 'bourbon' in user_input:
                expertise = 'bourbon'
            elif 'wine' in user_input:
                expertise = 'wine'
            elif 'beer' in user_input:
                expertise = 'beer'
            elif 'mezcal' in user_input:
                expertise = 'mezcal'
            elif 'tequila' in user_input:
                expertise = 'tequila'
            elif 'rye' in user_input:
                expertise = 'rye'
            elif 'whiskey' in user_input:
                expertise = 'whiskey'
            elif 'scotch' in user_input:
                expertise = 'scotch'
            else:
                expertise = 'general'

            # Define prompts for different expertise areas
            prompts = {
                'bourbon': "You are a veteran bartender that is considered an expert in bourbon. "
                           "You are a sommelier, a Cicerone, and a Bourbon Steward. "
                           "Please provide 3 bourbon recommendations for the guests with a brief explanation.",
                'wine': "You are a knowledgeable sommelier. "
                        "Please provide 3 wine recommendations for the guests with a brief explanation.",
                'beer': "You are a beer enthusiast. "
                        "Please provide 3 beer recommendations for the guests with a brief explanation.",
                'mezcal': "You are an expert in mezcal. "
                          "Please provide 3 mezcal recommendations for the guests with a brief explanation.",
                'tequila': "You are a tequila connoisseur. "
                           "Please provide 3 tequila recommendations for the guests with a brief explanation.",
                'rye': "You are a whiskey aficionado. "
                       "Please provide 3 rye whiskey recommendations for the guests with a brief explanation.",
                'whiskey': "You are an expert in whiskey. "
                           "Please provide 3 whiskey recommendations for the guests with a brief explanation.",
                'scotch': "You are a Scotch whisky connoisseur. "
                          "Please provide 3 Scotch whisky recommendations for the guests with a brief explanation.",
                'general': "I'm here to assist you with drink-related questions. "
                           "Please specify if you have any questions or need recommendations about bourbon, wine, beer, mezcal, tequila, rye, whiskey, or scotch."
            }

            prompt = prompts.get(expertise, prompts['general'])

            if 'clear_button' in request.POST:
                # Clear the prompt and question if the clear button is clicked
                user_input = ''
            else:
                # Include the user's question in the prompt
                prompt += "\n\n" + user_input

            try:
                response = openai.Completion.create(
                    engine='text-davinci-003',
                    prompt=prompt,
                    max_tokens=256,
                    temperature=0,
                )
                print(response)

                if response and response["choices"]:
                    chatbot_response = response["choices"][0]['text']

                    # Clean up the response by removing leading punctuation marks
                    chatbot_response = chatbot_response.lstrip(string.punctuation).strip()

                    # Remind the server if the question is not related to alcohol
                    if expertise == 'general' and 'alcohol' not in chatbot_response:
                        chatbot_response += "\n\nPlease remember that I'm here to assist you with drink-related questions."

            except Exception as e:
                # Handle the exception appropriately
                print(f"Error: {e}")

    return render(request, 'main.html', {'response': chatbot_response, 'user_input': user_input})




