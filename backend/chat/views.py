# this file validates the incoming data and routes it

import logging

from rest_framework import viewsets, status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import ChatSerializer
from .models import Chat
from .services import handle_chat_message


logger = logging.getLogger('app.chat')


# handles chat data and provides a custom endpoint to process chat message
class ChatViewSet(viewsets.ModelViewSet): # viewsets.ModelViewSet provides automatic CRUD actions for the Chat model
    queryset = Chat.objects.all().order_by('-created_at') # fetch all the chat records from the db, sorted by the newest first
    serializer_class = ChatSerializer # links the view to ChatSerializer to auto handle validation and coversion to/from JSON for CRUD operations.

    parser_classes = [FormParser, JSONParser] # limits the backend to only accept data sent as standard JSON or URL-encoded forms

    # action decorator creates a custom routing path inside the ViewSet
    # details=False means this endpoint acts on the whole collection, not a specific chat ID
    # this endpoint only accepts post requests
    # changes the URL slug name to fetch-chat -> /chat/fetch-chat [POST]
    @action(detail=False, methods=['post'], url_path='fetch-chat')
    def chat(self, request):
        # extract data from the incoming request payload
        user_message = request.data.get('message')
        state = request.data.get('state', {})
        idempotency_key = request.headers.get('Idempotency-Key') or request.data.get('idempotency_key')
        logger.info(
            'chat_message_received',
            extra={
                'event': 'chat_message_received',
                'known_fields': sorted(key for key, value in state.items() if value),
                'message_length': len(user_message or ''),
            },
        )

        # if 'message' key is missing, computation stops and returns bad request error
        if not user_message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # if 'message' exists, business logic is exectuted
        result = handle_chat_message(
            user_message=user_message,
            state=state,
            idempotency_key=idempotency_key,
        )

        response_status = result.pop('http_status', None)
        if response_status is None:
            response_status = status.HTTP_500_INTERNAL_SERVER_ERROR if result.get('error') else status.HTTP_201_CREATED
        logger.info(
            'chat_response_ready',
            extra={
                'event': 'chat_response_ready',
                'status_code': response_status,
                'next_step': result.get('next_step'),
                'result_status': 'error' if result.get('error') else 'success',
            },
        )

        # send the result back to the client/user with http code 201 confirming chat response was created successfully
        return Response(
            result,
            status=response_status
        )
        
