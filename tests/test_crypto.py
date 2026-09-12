from cryptography.fernet import Fernet, InvalidToken
import pytest

from common.crypto import decrypt, encrypt, encrypt_file, read_key


def test_encrypt_decrypt_round_trip() -> None:
    key = Fernet.generate_key()
    payload = b"small model payload"

    assert decrypt(encrypt(payload, key), key) == payload


def test_decrypt_with_another_key_fails() -> None:
    ciphertext = encrypt(b"small model payload", Fernet.generate_key())

    with pytest.raises(InvalidToken):
        decrypt(ciphertext, Fernet.generate_key())


def test_encrypt_file_uses_key_from_secret_file(tmp_path) -> None:
    key = Fernet.generate_key()
    key_path = tmp_path / "model.key"
    key_path.write_bytes(key + b"\n")
    source = tmp_path / "model.tar.gz"
    destination = tmp_path / "model.tar.gz.enc"
    source.write_bytes(b"archive bytes")

    encrypt_file(source, destination, read_key(key_path))

    assert decrypt(destination.read_bytes(), key) == b"archive bytes"
