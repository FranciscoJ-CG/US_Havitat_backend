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


class DictionariesView(APIView):

    def get(self, request):
        url = 'https://xc223xnsz1.execute-api.us-east-1.amazonaws.com/dev/v1/dictionaries/pse/banks'
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


def sign_in_to_coink(login_data):
    url = f"{settings.BAAS_API_URL}/users/sign_in"

    email = login_data.get("email")
    document_number = login_data.get("document_number")
    phone_number = login_data.get("phone_number")
    document_type_id = login_data.get("document_type_id")

    payload = {
        "pin": login_data.get("pin"),
        "method": login_data.get("method", "PHONE")
    }

    if email: payload['email'] = email
    if document_number: payload['document_number'] = document_number
    if phone_number: payload['phone_number'] = phone_number
    if document_type_id: payload['document_type_id'] = document_type_id


    headers = {
        'x-api-key': settings.COINK_X_API_KEY,
        'Content-Type': 'application/json'
    }
    encrypted_payload = Utils.get_cypher_payload(payload, settings.COINK_SECRET)

    data = {'payload': encrypted_payload}
    headers = {
        'x-api-key': settings.COINK_X_API_KEY,
        'Content-Type': 'application/json'
    }
    requests.post(url, json=data, headers=headers)

    response = requests.post(url, json=data, headers=headers)

    authorization_value = None

    if response.status_code == 200:
        payload = json.loads(response.text).get('payload')
        decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
        decrypted = json.loads(decrypted)
        authorization_value = decrypted.get('authorization')

    return authorization_value
    





coink_login_data = {
    "phone_number": "573180004115",
    "pin": "1212",
    "method": "PHONE"
}
class AccountHistoryView(APIView):

    def get(self, request):
        authorization_value = sign_in_to_coink(coink_login_data)

        url = f"{settings.BAAS_API_URL}/accounts/history"
        authorization =  authorization_value
        headers = {
            'Authorization': authorization,
            'x-api-key': settings.COINK_X_API_KEY,
            'Content-Type': 'application/json'
        }

        try:
            mocked_request_data = { 
                           "items_per_page": 1000,
                           "current_page": 1,
                           "filters": {
                               "account_id": "89ef1221-0782-453b-a874-fc63d9eeebab"
                               }
                           }

            encrypted = Utils.get_cypher_payload(mocked_request_data, settings.COINK_SECRET)
            # encrypted = Utils.get_cypher_payload(request.data, settings.COINK_SECRET)
            response = requests.post(url, json={'payload': encrypted}, headers=headers)
            data = response.json()
            
            payload = data.get('payload')
            decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
            return Response(json.loads(decrypted), status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as http_err:
            return Response({'error': str(http_err)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UserTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
        pending_transactions = [] 
        transactions_list = []

        for transaction in transactions:
            if transaction.status == 'completed':
                transactions_list.append(transaction)
            else:
                pending_transactions.append(transaction)
         
        for transaction in pending_transactions:
            status_id = BaaSConnection.get_updated_transaction_status(
                transaction.transfer_id, coink_login_data)
            is_active = BaaSConnection.update_transaction_and_admin_fees(transaction, status_id)
            if is_active:
                transactions_list.append(transaction)

        serializer = TransactionSerializer(transactions_list, many=True)
        return Response(serializer.data)


def generate_random_string(length=15):
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string



class PSETransaction(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, id):
        authorization = sign_in_to_coink(coink_login_data)

        url = f"{settings.BAAS_API_URL}/transactions/detail"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Authorization': authorization,
            'Content-Type': 'application/json'
        }

        payload = { 'transfer_id': id }
        encrypted = Utils.get_cypher_payload(payload, settings.COINK_SECRET)
        data = {'payload': encrypted}

        response = requests.post(url, json=data, headers=headers)
        data = response.json()
        payload = data.get('payload')
        decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
        decrypted = json.loads(decrypted)

        return Response(decrypted)
    


    def post(self, request, id):
        complex_id = id
        transfer_id = str(uuid.uuid4())
        external_reference = generate_random_string() 
        custom_id = generate_random_string()
        account_number = AccountInfo.objects.get(complex__id=complex_id).account_number
        callback = f'https://{settings.ALLOWED_HOSTS[0]}/transactions/callback',
        serializer = PSETransactionSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            admin_fees = AdminFee.objects.filter(id__in=data['admin_fee_ids'])
            total_amount = sum([admin_fee.get_total_to_pay() for admin_fee in admin_fees])

            if total_amount != data['amount']:
                return Response({
                    'total_amount': total_amount,
                    'data.amount': data['amount'],
                    'detail': 'Total amount does not match with admin fees'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            data['amount']=float(data['amount'])
            payload = {
                'transfer_id': transfer_id,
                'external_reference': external_reference,
                'custom_id': custom_id,
                'account_number': account_number,
                'callback': callback[0],
                'external_account': data['external_account'],
            }

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



@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def callback(request):
    print('........... callback...............')
    print(request.data)
    return Response({'headers':request.headers, 'data': request.data}, status=status.HTTP_200_OK)    
    





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
            response_data = response.json()
            print(response_data)
            decrypted = Utils.get_decrypt(response_data.get('payload'), settings.COINK_SECRET)

            return Response(json.loads(decrypted), status=response.status_code)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







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


class BaaSRegister(APIView):
    def post(self, request):
        data = {
            'user_info': request.data,
            'callback': f'{settings.ALLOWED_HOSTS[0]}/transactions/callback',
            'context_id': 4
        }
        # serializer = BaaSRegisterSerializer(data=data)
        if True:# serializer.is_valid():
            # data = serializer.validated_data
            response = self.register_user(data)
            payload = json.loads(response.text).get('payload')
            decrypted_response = self.decrypt_response(payload)
            if response.status_code == 200:
                return Response(decrypted_response, status=status.HTTP_200_OK)
            else:
                return Response(response, status=response.status_code)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def register_user(self, data):
        url = f"{settings.BAAS_API_URL}/forms/register"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Content-Type': 'application/json'
        }
        encrypted_data = Utils.get_cypher_payload(data, settings.COINK_SECRET)
        response = requests.post(url, json={'payload': encrypted_data}, headers=headers)
        return response

    def decrypt_response(self, response_text):
        try:
            decrypted = Utils.get_decrypt(response_text, settings.COINK_SECRET)
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return {"error": "Failed to decrypt response"}


class BaasRegisterStatus(APIView):
    def get(self, request):
        url = f"{settings.BAAS_API_URL}/forms/get/status?process_id={request.query_params.get('process_id')}"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print('response', response, response.text)
            payload = json.loads(response.text).get('payload')
            decrypted_response = self.decrypt_response(payload)
            return Response(decrypted_response, status=status.HTTP_200_OK)
        else:
            return Response(response.json(), status=response.status_code)

    def decrypt_response(self, response_text):
        try:
            decrypted = Utils.get_decrypt(response_text, settings.COINK_SECRET)
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return {"error": "Failed to decrypt response"}
        