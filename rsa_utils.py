from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import os

# Save keys permanently
def generate_keys():
    if not os.path.exists("private.pem") or not os.path.exists("public.pem"):
        key = RSA.generate(2048)

        with open("private.pem", "wb") as f:
            f.write(key.export_key())

        with open("public.pem", "wb") as f:
            f.write(key.publickey().export_key())

# Load keys
def load_keys():
    with open("private.pem", "rb") as f:
        private_key = RSA.import_key(f.read())

    with open("public.pem", "rb") as f:
        public_key = RSA.import_key(f.read())

    return private_key, public_key

# Encrypt password
def encrypt_password(password):
    generate_keys()
    private_key, public_key = load_keys()

    cipher = PKCS1_OAEP.new(public_key)
    encrypted = cipher.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()

# Decrypt password
def decrypt_password(enc_password):
    private_key, public_key = load_keys()

    cipher = PKCS1_OAEP.new(private_key)
    decrypted = cipher.decrypt(base64.b64decode(enc_password))
    return decrypted.decode()