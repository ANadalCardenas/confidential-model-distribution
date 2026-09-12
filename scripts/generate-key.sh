#!/usr/bin/env sh
set -eu

umask 077
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' > "${1:-model.key}"
echo "Wrote Fernet key to ${1:-model.key}"
