"""Small, authenticated-encryption helpers shared by distribution components."""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet


def read_key(key_path: str | Path) -> bytes:
    """Read a Fernet key from a secret file.

    Stripping a final newline makes keys created by the shell helper convenient to
    use, while Fernet still validates malformed keys when it is constructed.
    """
    return Path(key_path).read_bytes().strip()


def encrypt(data: bytes, key: bytes) -> bytes:
    """Return an authenticated Fernet ciphertext for *data*."""
    return Fernet(key).encrypt(data)


def decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """Verify and decrypt a Fernet ciphertext."""
    return Fernet(key).decrypt(ciphertext)


def encrypt_file(source: str | Path, destination: str | Path, key: bytes) -> Path:
    """Encrypt a file and return the destination path.

    The deliberately small demonstration model is first archived, so reading the
    archive at once keeps the implementation simple while retaining Fernet's
    authenticated-encryption properties.
    """
    source_path = Path(source)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_bytes(encrypt(source_path.read_bytes(), key))
    return destination_path
