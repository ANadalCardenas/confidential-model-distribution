#!/usr/bin/env python3
"""Download, encrypt, and publish a small Hugging Face model artifact."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from common.crypto import encrypt_file, read_key

DEFAULT_MODEL_ID = "hf-internal-testing/tiny-random-bert"
DEFAULT_ARTIFACT_NAME = "model.tar.gz.enc"


def package_model(model_directory: Path, archive_path: Path) -> Path:
    """Create ``model.tar.gz`` containing the downloaded model directory."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    # make_archive expects the suffixless base name when creating a gztar archive.
    base_name = archive_path.with_suffix("").with_suffix("")
    shutil.make_archive(str(base_name), "gztar", root_dir=model_directory)
    return archive_path


def build_artifact(
    model_id: str,
    key_path: Path,
    work_directory: Path,
    token: str | None = None,
) -> Path:
    """Download a model, archive it, and encrypt the archive locally."""
    model_directory = work_directory / "model"
    archive_path = work_directory / "model.tar.gz"
    encrypted_path = work_directory / DEFAULT_ARTIFACT_NAME

    work_directory.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=model_id,
        local_dir=model_directory,
        token=token,
    )
    package_model(model_directory, archive_path)
    return encrypt_file(archive_path, encrypted_path, read_key(key_path))


def upload_artifact(
    artifact_path: Path,
    repository_id: str,
    token: str,
    artifact_name: str = DEFAULT_ARTIFACT_NAME,
) -> str:
    """Upload only the encrypted artifact and return its Hub URL."""
    api = HfApi(token=token)
    return api.upload_file(
        path_or_fileobj=str(artifact_path),
        path_in_repo=artifact_name,
        repo_id=repository_id,
        repo_type="model",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default=os.getenv("SOURCE_MODEL_ID", DEFAULT_MODEL_ID))
    parser.add_argument("--repo-id", default=os.getenv("HF_REPO_ID"), help="Destination Hugging Face repository")
    parser.add_argument("--token", default=os.getenv("HF_TOKEN"), help="Hugging Face write token")
    parser.add_argument("--key-path", default=os.getenv("MODEL_KEY_PATH", "/run/secrets/model.key"))
    parser.add_argument("--work-dir", default=os.getenv("WORK_DIR", "/tmp/producer"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.repo_id:
        raise SystemExit("HF_REPO_ID is required")
    if not args.token:
        raise SystemExit("HF_TOKEN is required")

    artifact = build_artifact(
        model_id=args.model_id,
        key_path=Path(args.key_path),
        work_directory=Path(args.work_dir),
        token=args.token,
    )
    url = upload_artifact(artifact, args.repo_id, args.token)
    print(f"Uploaded encrypted model artifact: {url}")


if __name__ == "__main__":
    main()
