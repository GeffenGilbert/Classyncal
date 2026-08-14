from cryptography.fernet import Fernet

from app.config import TOKEN_ENCRYPTION_KEY

if not TOKEN_ENCRYPTION_KEY:
    raise RuntimeError(
        "TOKEN_ENCRYPTION_KEY is not set. Generate one with: "
        "python3 -c \"from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())\""
    )

_fernet = Fernet(TOKEN_ENCRYPTION_KEY)


def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()
