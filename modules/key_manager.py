from cryptography.fernet import InvalidToken

def encrypt(fernet_instance_with_key, message):
    return fernet_instance_with_key.encrypt(message.encode()).decode()

def decrypt(fernet_instance_with_key, message):
    try:
        return fernet_instance_with_key.decrypt(message.encode()).decode()
    except InvalidToken:
        return '-1'
        