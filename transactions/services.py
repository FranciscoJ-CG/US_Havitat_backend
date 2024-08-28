from django.conf import settings

from Crypto.Cipher import DES3
from Crypto.Hash import MD5
from Crypto.Util.Padding import unpad, pad
import base64, json, requests

from accounting.models import AdminFee

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
    
    
    @staticmethod
    def get_updated_transaction_status(transfer_id, coink_login_data):
        authorization = BaaSConnection.sign_in_to_coink(coink_login_data)

        url = f"{settings.BAAS_API_URL}/transactions/detail"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Authorization': authorization,
            'Content-Type': 'application/json'
        }

        payload = {'transfer_id': transfer_id}
        encrypted = Utils.get_cypher_payload(payload, settings.COINK_SECRET)
        data = {'payload': encrypted}

        response = requests.post(url, json=data, headers=headers)
        data = response.json()
        payload = data.get('payload')
        decrypted = Utils.get_decrypt(payload, settings.COINK_SECRET)
        decrypted = json.loads(decrypted)
        status_id = decrypted.get('operation_status_id')

        return status_id

    @staticmethod
    def update_transaction_and_admin_fees(transaction, status_id):
        admin_fees = AdminFee.objects.filter(transaction=transaction)
        is_active = True
        if status_id == 2:
            transaction.status = 'completed'
            transaction.save()
            for admin_fee in admin_fees:
                admin_fee.state = 'paid'
                admin_fee.save()
            return is_active 
        elif status_id in [8, 15]:
            transaction.status = 'processing'
            transaction.save()
            for admin_fee in admin_fees:
                admin_fee.state = 'processing'
                admin_fee.save()
            return is_active
        elif status_id in [4, 3, 6]:
            transaction.status = 'discarded'
            transaction.save()
            for admin_fee in admin_fees:
                admin_fee.state = 'pending'
                admin_fee.save()
        return not is_active
