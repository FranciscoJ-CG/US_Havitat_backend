# messaging/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import status
from django.conf import settings

from .services import send_message
from .models import Thread
from auth_app.models import User
from auth_app.serializers import UserSerializer 
from estate_admin.models import Relationship, Complex
from helpers.handle_exceptions import handle_exceptions

import requests


MSS_API_URL = settings.MSS_API_URL 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_box_view(request, complex_id, view):
    user = request.user
    page_size = request.GET.get('page_size', '20')
    page = request.GET.get('page', '1')
    try:
        page_size = int(page_size)
        page = int(page)
    except ValueError:
        return Response({'detail': 'page_size and page must be integers.'}, status=status.HTTP_400_BAD_REQUEST)

    app_name = settings.APP_NAME
    query = f"?page_size={page_size}&page={page}&scope={complex_id}"
    url = f"{MSS_API_URL}/message_box/{app_name}/{user.uuid}/{view}/{query}"

    try:
        response = requests.get(url)
    except requests.RequestException:
        return Response({'detail': 'Error connecting to message service.'}, status=status.HTTP_502_BAD_GATEWAY)

    if not response.ok:
        return Response({'detail': 'Failed to fetch messages'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = response.json()
    except ValueError:
        return Response({'detail': 'Invalid response from message service.'}, status=status.HTTP_502_BAD_GATEWAY)

    data = response.json()

    for r in data['results']:
        participants_ids = r['thread']['participants']
        participants = User.objects.filter(uuid__in=participants_ids).values('id','username')
        r['thread']['participants'] = participants

    return Response(data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def thread_view(request, thread_id=None):
    if request.method == 'GET':
        if not isinstance(thread_id, int):
            return Response({'detail': 'thread_id is not an integer'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        response = requests.get(
                url=f"{MSS_API_URL}/thread/{user.uuid}/{thread_id}/",
            )
        data = response.json()
        messages = data['messages']
        for m in messages:
            m['sender'] = UserSerializer(User.objects.get(uuid=m['sender_uuid'])).data

        participants_ids = data['participants']
        participants = User.objects.filter(uuid__in=participants_ids).values('id','username')
        data['participants'] = participants

        return Response(data)

    if request.method == 'DELETE':
        user = request.user
        thread_ids = request.data.get('thread_ids', [])

        if not isinstance(thread_ids, list):
            return Response({'detail': 'thread_ids is not a list'}, status=status.HTTP_400_BAD_REQUEST)

        response = requests.delete(
                url=f"{MSS_API_URL}/thread/{user.uuid}/",
                json={'thread_ids': thread_ids}
            )
        data = response.json()

        if not response.status_code == 200:
            return Response({'detail': 'Failed to delete threads'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request):
    sender = request.user

    thread_id = request.data.get('thread_id')
    recipient_id = request.data.get('recipient_id')
    subject = request.data.get('subject')
    priority = request.data.get('priority', 'low')
    body = request.data.get('body')
    complex_id = request.data.get('complex_id', None)

    try:
        if thread_id:
            if not isinstance(thread_id, int):
                raise ValueError('thread_id is not an integer') 
        if recipient_id:
            if not isinstance(recipient_id, int):
                raise ValueError('recipient_id is not an integer')
        if not subject or not subject.strip():
            raise ValueError('subject is missing')
        if not body or not body.strip():
            raise ValueError('body is missing')
        if priority not in ['low', 'medium', 'high']:
            raise ValueError('priority is invalid')
    except ValueError as e:
        return handle_exceptions('invalid_data', 'send_message_view', e, status.HTTP_400_BAD_REQUEST)

    recipient = get_object_or_404(User, id=recipient_id) if recipient_id else None
    thread = get_object_or_404(Thread, id=thread_id) if thread_id else None
    thread_id = thread_id if thread else None
    if not thread_id:
        complexes = Complex.objects.filter(id__in=[complex_id])
        if not complexes.exists(): 
            return Response({'detail': 'Complex not found'}, status=status.HTTP_404_NOT_FOUND)


    try:
        send_message(sender_id=sender.uuid,

                         subject=subject,
                         body=body,
                         complex_ids=complex_id,
                         writers=[recipient],
                         readers=[],
                         priority=priority, 
                         thread_id=thread_id,)
        return Response({'detail': 'Message sent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return handle_exceptions('unexpected_error', 'send_message_view -- send_message_api', e)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_notifications_view(request):
    sender = request.user

    subject = request.data.get('subject')
    priority = request.data.get('priority', 'low')
    body = request.data.get('body')
    complex_id = request.data.get('complex_id')

    try:
        if not subject or not subject.strip():
            raise ValueError('subject is missing')
        if not body or not body.strip():
            raise ValueError('body is missing')
        if priority not in ['low', 'medium', 'high']:
            raise ValueError('priority is invalid')
        if not complex_id or not isinstance(complex_id, int):
            raise ValueError('complex_id is missing or invalid')
    except ValueError as e:
        return handle_exceptions('invalid_data', 'send_notifications_view', e, status.HTTP_400_BAD_REQUEST)

    try:
        complex_instance = Complex.objects.get(id=complex_id)
    except Complex.DoesNotExist:
        return Response({'detail': 'Complex not found'}, status=status.HTTP_400_BAD_REQUEST)

    user_ids = Relationship.objects.filter(unit__complex_id=complex_id).values_list('user_id', flat=True)
    receivers = User.objects.filter(id__in=user_ids)
    if not receivers.exists():
        return Response({'detail': 'No users found in the specified complex'}, status=status.HTTP_409_CONFLICT)

    try:
        send_message(
            sender_id=sender.uuid,
            subject=subject,
            body=body,
            complex_ids=complex_id,
            writers=[],
            readers=receivers,
            priority=priority,
            tags='notification',)
        return Response({'detail': 'Message sent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return handle_exceptions('unexpected_error', 'send_notifications_view -- send_message_api', e)

