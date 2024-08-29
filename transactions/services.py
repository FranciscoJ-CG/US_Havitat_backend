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

        payload = {
            "pin": login_data.get("pin"),
            "method": login_data.get("method", "PHONE"),
            "email": login_data.get("email"),
            "document_number": login_data.get("document_number"),
            "phone_number": login_data.get("phone_number"),
            "document_type_id": login_data.get("document_type_id")
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
    def get_updated_transaction_status(transfer_id, coink_login_data):
        authorization = BaaSConnection.sign_in_to_coink(coink_login_data)

        if not authorization:
            return None

        url = f"{settings.BAAS_API_URL}/transactions/detail"
        headers = {
            'x-api-key': settings.COINK_X_API_KEY,
            'Authorization': authorization,
            'Content-Type': 'application/json'
        }

        payload = {'transfer_id': transfer_id}
        encrypted = Utils.get_cypher_payload(payload, settings.COINK_SECRET)

        try:
            response = requests.post(url, json={'payload': encrypted}, headers=headers)
            response.raise_for_status()
            decrypted = Utils.get_decrypt(response.json().get('payload'), settings.COINK_SECRET)
            return json.loads(decrypted).get('operation_status_id')
        except Exception as e:
            return None


    @staticmethod
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
