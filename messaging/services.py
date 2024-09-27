# messaging/services.py
from django.db import transaction
from django.conf import settings

import requests
import json

@transaction.atomic
def send_message(sender_id,
                     subject,
                     body,
                     complex_ids,
                     writers,
                     readers, 
                     priority=None,
                     thread_id=None,
                     tags='',):

    scope = ','.join(str(complex_ids))
    writers_ids = [str(w.uuid) for w in writers]
    readers_ids = [str(r.uuid) for r in readers]
   
    params = {
        "belongs_to": settings.APP_NAME,
        "writers_ids": writers_ids,
        "readers_ids": readers_ids,
        "scope": scope,
        "subject": subject,
        "body": body,
        "priority": priority,
        "thread_id": thread_id,
        "tags": tags,
    }
    
    response = requests.post(
        url=f"{settings.MSS_API_URL}/send_message/{sender_id}/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(params)
    )
    
    if not response.ok:
        raise Exception("Error sending message")

    return response
