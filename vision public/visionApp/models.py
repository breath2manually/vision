from django.db import models

class Character(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    personality = models.TextField()
    initial_message = models.TextField()
    scenario = models.TextField()
    example_dialogues = models.TextField()

class Conversation(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE, null=True)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_user = models.BooleanField(default=True)

class ChatbotConfiguration(models.Model):
    personality = models.TextField()

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)
