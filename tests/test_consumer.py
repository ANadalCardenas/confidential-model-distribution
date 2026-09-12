import io
import tarfile

from cryptography.fernet import Fernet

from common.crypto import encrypt


def test_decrypt_and_extract_reads_runtime_key(tmp_path) -> None:
    # Import here so the crypto test suite does not need the consumer's optional
    # Hugging Face/Transformers runtime dependencies.
    from consumer.consumer import decrypt_and_extract

    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        payload = b'{"model_type": "bert"}'
        info = tarfile.TarInfo("config.json")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))

    key = Fernet.generate_key()
    key_path = tmp_path / "runtime-secret.key"
    key_path.write_bytes(key + b"\n")
    encrypted_path = tmp_path / "model.tar.gz.enc"
    encrypted_path.write_bytes(encrypt(archive.getvalue(), key))
    model_directory = tmp_path / "model"

    assert decrypt_and_extract(encrypted_path, key_path, model_directory) == model_directory
    assert (model_directory / "config.json").read_bytes() == b'{"model_type": "bert"}'
    assert not (tmp_path / "model.tar.gz").exists()
