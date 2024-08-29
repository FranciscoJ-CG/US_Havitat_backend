# transactions/views.py
from django.conf import settings
from django.core.cache import cache
from  django.db import transaction as django_transaction

from rest_framework import  status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view

import  uuid, requests, json, secrets, string
from datetime import datetime

from .models import Transaction, AccountInfo
from .serializers import (TransactionSerializer,
                          PSETransactionSerializer,
                          )
from .services import  Utils, BaaSConnection
from accounting.models import AdminFee



coink_login_data = {
    "phone_number": "573180004115",
    "pin": "1212",
    "method": "PHONE"
}

class DictionariesView(APIView):

    def get(self, request):
        url = f"{settings.BAAS_API_URL}/dictionaries/pse/banks"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() 
            data = response.json()
            payload = data.get('payload')
            decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
            return Response(json.loads(decrypted), status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as http_err:
            return Response({'error': str(http_err)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
           return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountHistoryView(APIView):

    # def post(self, request):
    def get(self, request):
        authorization_value = BaaSConnection.sign_in_to_coink(coink_login_data)

        if not authorization_value:
            return Response({'error': 'Failed to authenticate'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        url = f"{settings.BAAS_API_URL}/accounts/history"
        authorization =  authorization_value
        headers = {
            'Authorization': authorization,
            'x-api-key': settings.COINK_X_API_KEY,
            'Content-Type': 'application/json'
        }

        mocked_request_data = { 
            "items_per_page": 1000,
            "current_page": 1,
            "filters": {"account_id": "89ef1221-0782-453b-a874-fc63d9eeebab"}
        }

        try:
            encrypted = Utils.get_cypher_payload(mocked_request_data, settings.COINK_SECRET)
            # encrypted = Utils.get_cypher_payload(request.data, settings.COINK_SECRET)
            response = requests.post(url, json={'payload': encrypted}, headers=headers)
            decrypted = Utils.get_decrypt(response.json().get('payload'), settings.COINK_SECRET)

            return Response(json.loads(decrypted), status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as http_err:
            return Response({'error': str(http_err)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')

        pending_transactions = [t for t in transactions if t.status != 'completed']
        relevant_transactions = [t for t in transactions if t.status == 'completed']

        for transaction in pending_transactions:
            status_id = BaaSConnection.get_updated_transaction_status(transaction.transfer_id, coink_login_data)
            is_active = BaaSConnection.update_transaction_and_admin_fees(transaction, status_id)
            if is_active: relevant_transactions.append(transaction)
         
        serializer = TransactionSerializer(relevant_transactions, many=True)
        return Response(serializer.data)

        

@api_view(['GET'])
def callback(request):
    return Response({'headers': request.headers, 'data': request.data}, status=status.HTTP_200_OK)


def generate_random_string(length=15):
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string


class PSETransaction(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        authorization = BaaSConnection.sign_in_to_coink(coink_login_data)
        if not authorization:
            return Response({'error': 'Failed to authenticate'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = f"{settings.BAAS_API_URL}/transactions/detail"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Authorization': authorization,
            'Content-Type': 'application/json'
        }

        payload = { 'transfer_id': id }
        try:
            encrypted = Utils.get_cypher_payload(payload, settings.COINK_SECRET)
            response = requests.post(url, json={'payload': encrypted}, headers=headers)
            decrypted = Utils.get_decrypt(response.json().get('payload'), settings.COINK_SECRET)
            return Response(json.loads(decrypted), status=status.HTTP_200_OK)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, id):
        complex_id = id
        transfer_id = str(uuid.uuid4())
        external_reference = generate_random_string() 
        custom_id = generate_random_string()
        account_number = AccountInfo.objects.get(complex__id=complex_id).account_number
        callback = f'https://{settings.ALLOWED_HOSTS[0]}/transactions/callback',
        serializer = PSETransactionSerializer(data=request.data)

        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        admin_fees = AdminFee.objects.filter(id__in=data['admin_fee_ids'])
        total_amount = sum([admin_fee.get_total_to_pay() for admin_fee in admin_fees])

        if total_amount != data['amount']:
            return Response({
                'total_amount': total_amount,
                'data.amount': data['amount'],
                'detail': 'Total amount does not match with admin fees'}, 
                status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'transfer_id': transfer_id,
            'external_reference': external_reference,
            'custom_id': custom_id,
            'account_number': account_number,
            'callback': callback[0],
            'external_account': data['external_account'],
        }


        data['amount']=float(data['amount'])
        response = None
        with django_transaction.atomic():
            transaction = Transaction.objects.create(
                user = request.user,
                amount = data['amount'],
                timestamp =  datetime.now(), 
                transfer_id = transfer_id,
                )
            transaction.save()

            for admin_fee in admin_fees:
                if admin_fee.transaction is not None:
                    existing_transaction = Transaction.objects.get(id=admin_fee.transaction.id)
                    existing_transaction.status = 'discarded'
                    existing_transaction.save()

                admin_fee.transaction = transaction
                admin_fee.paid_interest = admin_fee.get_interest_price()
                admin_fee.save()

            response = self.send_pse_transaction({**payload, **data})

        if response is None or 'error' in response:
            return Response({'detail': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response, status=status.HTTP_201_CREATED)

    def send_pse_transaction(self, data):
        url = f"{settings.BAAS_API_URL}/transactions/paygateway/pse"
        headers = {
            'Authorization':'1234',
            'x-api-key': settings.COINK_X_API_KEY, 
            'Content-Type': 'application/json'
        }
        try:
            payload = Utils.get_cypher_payload(data, settings.COINK_SECRET)
            response = requests.post(url, json={'payload': payload}, headers=headers)
            decrypted = Utils.get_decrypt(response.json().get('payload'), settings.COINK_SECRET)
            return json.loads(decrypted)
        except Exception as err:
            return {"error": str(err)}


class AccountOwnView(APIView):
    def get(self, request):
        api_key = settings.COINK_X_API_KEY 
        url = 'https://xc223xnsz1.execute-api.us-east-1.amazonaws.com/dev/v1/accounts/own'
        authorization = cache.get('authorization')

        headers = {
            'Authorization': authorization,
            'x-api-key': api_key,
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            decrypted = Utils.get_decrypt(response.json().get('payload'), settings.COINK_SECRET)
            return Response(json.loads(decrypted), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# just for testing in development
class PSETestTransaction(APIView):
    def get(self, request ):
        transfer_id = str(uuid.uuid4())
        external_reference = generate_random_string() 
        custom_id = generate_random_string()
        account_number = '00000005475' 
        callback = f'https://{settings.ALLOWED_HOSTS[0]}/transactions/callback',
        data = {
            "subject":"transaction subject text",
            "external_account":{"bank_id":20},
            "amount":10000,
            "admin_fee_ids":[1,2]
            }
 
        serializer = PSETransactionSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data

            data['amount']=float(data['amount'])
            payload = {
                'transfer_id': transfer_id,
                'external_reference': external_reference,
                'custom_id': custom_id,
                'account_number': account_number,
                'callback': callback[0],
                'external_account': data['external_account'],
            }

            response = self.send_pse_transaction({**payload, **data})

            if response is None:
                return Response({'detail': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not 'error' in response:
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def send_pse_transaction(self, data):
        url = f"{settings.BAAS_API_URL}/transactions/paygateway/pse"
        headers = {
            'Authorization':'1234',
            'x-api-key': settings.COINK_X_API_KEY, 
            'Content-Type': 'application/json'
        }

        payload = Utils.get_cypher_payload(data, settings.COINK_SECRET)
        response = requests.post(url, json={'payload': payload}, headers=headers)
        response_data = json.loads(response.text)
        payload = response_data.get('payload')
        if payload is None:
            return {"error": response_data}
        decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
        decrypted = json.loads(decrypted)
        return decrypted 
