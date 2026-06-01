# this file registers the app

from django.apps import AppConfig # base class from django core used to configure an application's metadata and behaviour


class ChatConfig(AppConfig): # creates a custom configure class for Chat app
    name = 'chat'
