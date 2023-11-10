import json
from channels.generic.websocket import AsyncWebsocketConsumer
import openai
import asyncio
from visionApp.models import Message, ChatbotConfiguration, Character, Conversation
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def send_complete_signal(self):
        await self.send(text_data=json.dumps({'message_complete': True}))

    @database_sync_to_async
    def save_user_message(self, message_text, conversation):
        user_message = Message(text=message_text, is_user=True, conversation=conversation)
        user_message.save()
        return user_message
        
    @database_sync_to_async
    def save_ai_message(self, message_text, conversation):
        ai_message = Message(text=message_text, is_user=False, conversation=conversation)
        ai_message.save()
        return ai_message
        

    @database_sync_to_async
    def get_all_messages(self):
        return list(Message.objects.all())

    @database_sync_to_async
    def get_latest_personality(self):
        chatbot_config = ChatbotConfiguration.objects.latest('id')
        return chatbot_config.personality if chatbot_config else "You are a knowledgeable and concise assistant."

    @database_sync_to_async
    def change_personality(self, new_personality):
        try:
            chatbot_config = ChatbotConfiguration.objects.latest('id')
            chatbot_config.personality = new_personality
            chatbot_config.save()
        except ChatbotConfiguration.DoesNotExist:
            # Handle the case where no ChatbotConfiguration exists, if necessary.
            ChatbotConfiguration.objects.create(personality=new_personality)
        except Exception as e:
            # Optional: handle any other exception that might occur.
            print(f"An error occurred: {e}")

    @database_sync_to_async
    def get_or_create_character(self, character_name):
        character, created = Character.objects.get_or_create(name=character_name)
        return character

    @database_sync_to_async
    def get_or_create_conversation(self, character):
        conversation, created = Conversation.objects.get_or_create(character=character)
        return conversation

    @database_sync_to_async
    def get_character_messages(self, character):
        conversation = Conversation.objects.get(character=character)
        return list(conversation.messages.all())

    async def receive(self, text_data):
        data = json.loads(text_data)
        character_name = data.get('character')
        character = await self.get_or_create_character(character_name)
        
        # Check if the incoming message is a command to change the chatbot's personality.
        if 'command' in data and data['command'] == 'change_personality':
            # If it's a personality change command, retrieve the new personality from the message.
            new_personality = data.get('new_personality')
            if new_personality:
                # Parse the new personality JSON string.
                new_personality_data = json.loads(new_personality)
                
                # Update the character's personality attributes.
                character.details = new_personality_data.get('details', '')
                character.scenario = new_personality_data.get('scenario', '')
                character.personality = new_personality_data.get('personality', '')
                character.examples = new_personality_data.get('examples', [])
                
                # Call the method that updates the chatbot's personality in the database.
                await self.change_personality(new_personality)
        else:
            # If it's not a command, assume it's a regular chat message.
            message_text = data.get('message')
            if message_text:
                conversation = await self.get_or_create_conversation(character)
                # Save the user's message to the database.
                await self.save_user_message(message_text, conversation)

                # Construct the messages list for OpenAI input.
                messages = [{"role": "system", "content": character.personality}]

                # Retrieve the current chatbot personality.
                personality_text = await self.get_latest_personality()

                # Add all previous messages to the list.
                character_messages = await self.get_character_messages(character)
                for message in character_messages:
                    role = "user" if message.is_user else "assistant"
                    messages.append({"role": role, "content": message.text})

                # Add the current personality as a system message.
                messages.append({"role": "system", "content": personality_text})

                # Call OpenAI's API here with the 'messages' structure.
                openai.api_key = 'sk-'
                response = openai.ChatCompletion.create(
                    #model='gpt-3.5-turbo',
                    model='gpt-4-1106-preview',
                    messages=messages,
                    temperature=0.6,
                    max_tokens=2000,
                    stream=True
                )

                # Process the response from OpenAI to generate the chatbot's reply.
                collected_messages = []
                for message_chunk in response:
                    chunk_message = message_chunk['choices'][0]['delta']
                    if 'content' in chunk_message:
                        collected_messages.append(chunk_message['content'])
                        await self.send(text_data=json.dumps({'message_chunk': chunk_message['content']}))
                        await asyncio.sleep(0.0001)  # This delay may need adjustment.

                # Combine the chunks to form the full message.
                chatbot_message = ''.join(collected_messages).strip()

                # Save the AI's message to the database.
                await self.save_ai_message(chatbot_message, conversation)

                # Send the full message to the frontend.
                await self.send_complete_signal()
