import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a key from the password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_file(input_file: str, password: str):
    """Encrypts a file with the given password."""
    salt = os.urandom(16)
    key = derive_key(password, salt)
    fernet = Fernet(key)

    with open(input_file, 'rb') as f:
        data = f.read()

    encrypted_data = fernet.encrypt(data)

    # Save salt + encrypted data to new file
    with open(input_file + '.enc', 'wb') as f:
        f.write(salt + encrypted_data)
    
    os.remove(input_file)


def decrypt_file(encrypted_file: str, password: str):
    """Decrypts a file with the given password."""
    with open(encrypted_file, 'rb') as f:
        content = f.read()

    salt = content[:16]
    encrypted_data = content[16:]
    key = derive_key(password, salt)
    fernet = Fernet(key)

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception as e:
        return

    original_file = encrypted_file.replace('.enc', '')
    with open(original_file, 'wb') as f:
        f.write(decrypted_data)

    
