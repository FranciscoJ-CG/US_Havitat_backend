# messaging/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import status

from .serializers import MessageSerializer, MassiveMessageInputSerializer, ThreadStatusSerializer
from .services import send_message, send_massive_message
from .models import Thread, Message, ThreadStatus
from auth_app.models import User
from estate_admin.models import Relationship, Complex


class CustomPagination(PageNumberPagination):
    page_size = 5  
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_box_view(request, complex_id, view):
    user = request.user

    view_filter = {
        'inbox': {'in_inbox': True},
        'outbox': {'in_outbox': True},
    }.get(view, {})

    filter_args ={**view_filter, **{
        'user': user,
        'is_deleted': False,
        'thread__complex_id': complex_id
    }}

    thread_statuses = ThreadStatus.objects.filter(**filter_args).order_by('-last_message_date')
    
    paginator = CustomPagination()
    result_page = paginator.paginate_queryset(thread_statuses, request)

    serializer = ThreadStatusSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)



@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def thread_view(request, thread_id):
    user = request.user
    thread = get_object_or_404(Thread, id=thread_id)
    thread_status = get_object_or_404(ThreadStatus, user=user, thread=thread, is_deleted=False)
        
    if request.method == 'GET':

        thread_status.is_read = True
        thread_status.save()
        messages = Message.objects.filter(thread=thread)
        if not messages.exists():
            return Response({'detail': 'Not found.'}, status=404)
        
        message_serializer = MessageSerializer(messages, many=True)
        return Response({
            'subject': thread.subject,
            'messages': message_serializer.data,
            'participants': thread.participants.all().values('id', 'username')
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_threads_view(request):
    user = request.user
    thread_ids = request.data.get('thread_ids', [])
    
    if not thread_ids:
        return Response({'error': 'No thread IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count = ThreadStatus.objects.filter(user=user, id__in=thread_ids).update(is_deleted=True)
 
    return Response({
        'success': f'{deleted_count} threads marked as deleted',
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request):
    sender = request.user
    recipient_id = request.data.get('recipient_id')
    subject = request.data.get('subject')
    body = request.data.get('body')
    thread_id = request.data.get('thread_id', None)
    complex_id = request.data.get('complex_id', None)

    recipient = get_object_or_404(User, id=recipient_id) if recipient_id else None
    thread = get_object_or_404(Thread, id=thread_id) if thread_id else None
    complex = get_object_or_404(Complex, id=complex_id) if complex_id else None

    message = send_message(sender, recipient, subject, body, thread, complex)

    if message:
        return Response({'detail': 'Message sent successfully'}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Failed to send message'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_massive_message_view(request):
    sender = request.user
    serializer = MassiveMessageInputSerializer(data=request.data)

    if serializer.is_valid():
        subject = serializer.validated_data['subject']
        body = serializer.validated_data['body']
        complex_id = serializer.validated_data['complex_id']
        user_ids = Relationship.objects.filter(unit__complex_id=complex_id).values_list('user_id', flat=True)
        receivers = User.objects.filter(id__in= user_ids)
        complex = Complex.objects.get(id=complex_id)

        send_massive_message(sender, subject, body, receivers, complex)
        return Response({'detail': 'Massive message sent successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
