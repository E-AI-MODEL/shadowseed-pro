#!/bin/sh
# Decrypt only the author's output bundle. Never upload private key to GitHub.
set -eu
if [ "$#" -ne 3 ]; then
  echo 'Usage: decrypt_owner_artifact.sh encrypted_github_artifact.zip OWNER_PRIVATE.pem output_directory' >&2
  exit 2
fi
artifact=$1
private_key=$2
output=$3
umask 077
mkdir -p "$output"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT HUP INT TERM
unzip -oq "$artifact" -d "$work"
(cd "$work" && sha256sum -c SHA256SUMS)
openssl pkeyutl -decrypt \
  -inkey "$private_key" -in "$work/aes-key.rsa-oaep" -out "$work/secret-aes-key" \
  -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -in "$work/private-payload.aes" -out "$work/owner-data.tar.gz" \
  -pass "file:$work/secret-aes-key"
tar -xzf "$work/owner-data.tar.gz" -C "$output"
cp "$work/public-status.json" "$output/public-status.json"
echo 'Decryption finished. Keep owner-unblind.json away from independent reviewers.'
