#!/usr/bin/env python3
"""Download, decrypt, extract, and load a confidential model artifact."""

from __future__ import annotations

import argparse
import os
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING


from common.crypto import decrypt, read_key

if TYPE_CHECKING:
    from transformers import PreTrainedModel

DEFAULT_ARTIFACT_NAME = "model.tar.gz.enc"


def download_artifact(
    repository_id: str,
    destination_directory: Path,
    artifact_name: str = DEFAULT_ARTIFACT_NAME,
    token: str | None = None,
) -> Path:
    """Download the encrypted artifact from a Hugging Face model repository."""
    # Keep pure decrypt/extract helpers importable for the offline unit suite.
    from huggingface_hub import hf_hub_download
    destination_directory.mkdir(parents=True, exist_ok=True)
    return Path(
        hf_hub_download(
            repo_id=repository_id,
            filename=artifact_name,
            repo_type="model",
            token=token,
            local_dir=destination_directory,
        )
    )


def _extract_archive(archive_path: Path, model_directory: Path) -> None:
    """Extract a model archive without allowing paths outside *model_directory*."""
    model_directory.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:gz") as archive:
        try:
            # Python 3.12's data filter rejects absolute paths, traversal, links,
            # and special files. It is appropriate because model archives only
            # contain regular files and directories.
            archive.extractall(model_directory, filter="data")
        except TypeError:  # pragma: no cover - compatibility with older Python
            root = model_directory.resolve()
            for member in archive.getmembers():
                target = (root / member.name).resolve()
                if not target.is_relative_to(root) or member.issym() or member.islnk():
                    raise tarfile.TarError(f"unsafe archive member: {member.name}")
            archive.extractall(model_directory)


def decrypt_and_extract(
    encrypted_path: Path,
    key_path: Path,
    model_directory: Path,
) -> Path:
    """Read the runtime secret, decrypt *encrypted_path*, and extract its model."""
    archive_path = encrypted_path.with_suffix("")
    archive_path.write_bytes(decrypt(encrypted_path.read_bytes(), read_key(key_path)))
    try:
        _extract_archive(archive_path, model_directory)
    finally:
        # The plaintext archive is only an intermediate; extracted model files are
        # needed for loading, while retaining the archive is unnecessary.
        archive_path.unlink(missing_ok=True)
    return model_directory


def load_model(model_directory: Path) -> "PreTrainedModel":
    """Load the decrypted model without making any further network requests."""
    from transformers import AutoModel
    return AutoModel.from_pretrained(model_directory, local_files_only=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", default=os.getenv("HF_REPO_ID"), help="Source Hugging Face repository")
    parser.add_argument("--token", default=os.getenv("HF_TOKEN"), help="Hugging Face token for private repositories")
    parser.add_argument("--artifact-name", default=os.getenv("ARTIFACT_NAME", DEFAULT_ARTIFACT_NAME))
    parser.add_argument("--key-path", default=os.getenv("MODEL_KEY_PATH", "/run/secrets/model.key"))
    parser.add_argument("--work-dir", default=os.getenv("WORK_DIR", "/tmp/consumer"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.repo_id:
        raise SystemExit("HF_REPO_ID is required")

    work_directory = Path(args.work_dir)
    encrypted_path = download_artifact(
        repository_id=args.repo_id,
        destination_directory=work_directory / "download",
        artifact_name=args.artifact_name,
        token=args.token,
    )
    model_directory = decrypt_and_extract(
        encrypted_path=encrypted_path,
        key_path=Path(args.key_path),
        model_directory=work_directory / "model",
    )
    model = load_model(model_directory)
    print(f"Successfully loaded decrypted model: {model.__class__.__name__}")


if __name__ == "__main__":
    main()
