from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from Crypto.Cipher import DES3
from Crypto.Hash import MD5
from Crypto.Util.Padding import unpad, pad
import base64, json, requests

from accounting.models import AdminFee

from transactions.models import Transaction, AccountInfo
from transactions.serializers import TransactionSerializer



CONFIG = {
    'mode': DES3.MODE_ECB,
    'block_size': DES3.block_size
}

def encrypt_triple_des(message, key):
    to_encrypt = pad(message.encode('utf-8'), CONFIG['block_size'])
    cipher = DES3.new(get_key_triple_des(key), CONFIG['mode'])
    encrypted = cipher.encrypt(to_encrypt)
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_triple_des(message, key):
    encrypted = base64.b64decode(message)
    cipher = DES3.new(get_key_triple_des(key), CONFIG['mode'])
    decrypted = cipher.decrypt(encrypted)
    return unpad(decrypted, CONFIG['block_size']).decode('utf-8')

def get_key(key):
    return MD5.new(key.encode('utf-8')).digest()

def get_key_triple_des(key):
    security_key = MD5.new(key.encode('utf-8')).hexdigest()
    security_key += security_key[:16]
    return bytes.fromhex(security_key)

class Utils:
    @staticmethod
    def get_cypher_payload(obj, secret_key):
        return encrypt_triple_des(json.dumps(obj), secret_key)

    @staticmethod
    def get_decrypt(obj, secret_key):
        return decrypt_triple_des(obj, secret_key)

    @staticmethod
    def get_cypher_payload_with_api_key(obj, key):
        return encrypt_triple_des(json.dumps(obj), key)

        
class BaaSConnection:

    @staticmethod
    def api_call(complex_id, url, request_data=None, method='POST', headers=None):
        account_info = AccountInfo.objects.get(complex=complex_id)
        phone_number = account_info.phone_number
        pin = account_info.pin

        authorization = cache.get(f'authorization_{complex_id}')
        if not authorization:
            authorization = BaaSConnection.sign_in(phone_number, pin)
            cache.set(f'authorization_{complex_id}', authorization, 60*60)

        if headers is None:
            headers = {
                'Authorization': authorization,
                'x-api-key': settings.COINK_X_API_KEY,
                'Content-Type': 'application/json'
            }
        else:
            headers['Authorization'] = authorization

        try:
            if request_data and method.upper() == 'POST':
                encrypted_data = Utils.get_cypher_payload(request_data, settings.COINK_SECRET)
            
            if method.upper() == 'POST':
                response = requests.post(url, json={'payload': encrypted_data}, headers=headers)
            elif method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if str(response.status_code).startswith('4'):
                authorization = BaaSConnection.sign_in(phone_number, pin)
                cache.set(f'authorization_{complex_id}', authorization, 60*60)
                headers['Authorization'] = authorization

                if method.upper() == 'POST':
                    response = requests.post(url, json={'payload': encrypted_data}, headers=headers)
                elif method.upper() == 'GET':
                    response = requests.get(url, headers=headers)

            response.raise_for_status()
            decrypted_data = Utils.get_decrypt(response.json().get('payload'), settings.COINK_SECRET)
            return decrypted_data
        except requests.exceptions.HTTPError as http_err:
            raise http_err
        except Exception as err:
            raise err

    
    @staticmethod
    def sign_in(phone_number, pin):

        url = f"{settings.BAAS_API_URL}/users/sign_in"

        payload = {
            "phone_number": phone_number,
            "pin": pin,
            "method": "PHONE",
        }

        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Content-Type': 'application/json'
        }

        encrypted_payload = Utils.get_cypher_payload({k: v for k, v in payload.items() if v}, settings.COINK_SECRET)
        response = requests.post(url, json={'payload': encrypted_payload}, headers=headers)


        if response.status_code == 200:
            payload = json.loads(response.text).get('payload')
            decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
            return json.loads(decrypted).get('authorization')

        return None
        
    
    @staticmethod
    def get_updated_transaction_status(transfer_id, complex_id):
        url = f"{settings.BAAS_API_URL}/transactions/detail"
        payload = {'transfer_id': transfer_id}

        try:
            decrypted_response = BaaSConnection.api_call(complex_id, url, request_data=payload, method='POST')
            return json.loads(decrypted_response).get('operation_status_id')
        except Exception as e:
            return None


def update_transaction_and_admin_fees(transaction, status_id):
    admin_fees = AdminFee.objects.filter(transaction=transaction)

    status_mapping = {
        2: ('completed', 'paid'),
        8: ('processing', 'processing'),
        15: ('processing', 'processing'),
        4: ('discarded', 'pending'),
        3: ('discarded', 'pending'),
        6: ('discarded', 'pending')
    }

    transaction_status, admin_fee_status = status_mapping.get(status_id, (None, None))

    is_active = False

    if transaction_status:
        transaction.status = transaction_status
        transaction.save()

        for admin_fee in admin_fees:
            admin_fee.state = admin_fee_status
            admin_fee.save()
        is_active = transaction_status != 'discarded'

    return is_active



def fetch_transactions(complex_id):
    account_id = get_object_or_404(AccountInfo, complex=complex_id).account_id

    history_url = f"{settings.BAAS_API_URL}/accounts/history"
    account_own_url = f"{settings.BAAS_API_URL}/accounts/own"

    history_request_data = {
        "items_per_page": 4,
        "current_page": 1,
        "filters": {"account_id": str(account_id)}
    }

    decrypted_history_response = BaaSConnection.api_call(complex_id, history_url, request_data=history_request_data)
    decrypted_account_own_response = BaaSConnection.api_call(complex_id, account_own_url, method='GET')

    history = json.loads(decrypted_history_response)
    account_own = json.loads(decrypted_account_own_response)

    transactions = []
    for item in history.get('items'):
        transfer_id = item.get('transfer_id')
        try:
            transaction = Transaction.objects.get(transfer_id=transfer_id)
            serializer = TransactionSerializer(transaction)
            transactions.append(serializer.data)
        except Transaction.DoesNotExist:
            continue

    return {'transactions': transactions, 'account_info': account_own}