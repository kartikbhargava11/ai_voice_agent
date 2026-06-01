# this file defines the structure of the chat data to be stored in the database

from django.db import models # core django module used to define database fields, relationships and constraints

class Chat(models.Model):
    message = models.CharField(max_length=500) # creates a standard text column in the db
    created_at = models.DateTimeField(auto_now_add=True) # stores the date and time when the chat entry is first created
    updated_at = models.DateTimeField(auto_now=True) # stores the date and time whenever the chat entry is modified