import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class PasswordEncryption:
    def __init__(self):
        # Use environment variable or generate a new key
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)

    def _get_or_create_key(self):
        """Get existing key from environment or create a new one."""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Generate a new key using PBKDF2
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
            os.environ['ENCRYPTION_KEY'] = key.decode()
        else:
            key = key.encode()
        return key

    def encrypt(self, password: str) -> str:
        """Encrypt a password."""
        return self.fernet.encrypt(password.encode()).decode()

    def decrypt(self, encrypted_password: str) -> str:
        """Decrypt a password."""
        try:
            return self.fernet.decrypt(encrypted_password.encode()).decode()
        except Exception:
            return None

# Create a global instance
password_encryption = PasswordEncryption()
