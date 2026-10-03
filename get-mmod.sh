#!/bin/bash
# Download a release; never compile on the destination PC.
set -euo pipefail
repo=${1:?Usage: bash get-mmod.sh OWNER/REPO vVERSION --bind LOCAL_IP [install options]}
tag=${2:?Supply release tag}
shift 2
[[ $repo =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ && $tag =~ ^v[0-9A-Za-z.+-]+$ ]] || exit 1
[[ $(id -u) == 0 ]] || { echo 'Run as root'; exit 1; }
command -v curl >/dev/null || { echo 'Install curl and ca-certificates first'; exit 1; }
command -v python3 >/dev/null || { echo 'Install python3 first'; exit 1; }
stage=$(mktemp -d /tmp/mmod-release.XXXXXXXX)
trap 'rm -rf -- "$stage"' EXIT
version=${tag#v}
asset="mmod-stack-$version-debian13-amd64.tar.gz"
base="https://github.com/$repo/releases/download/$tag"
curl --fail --show-error --location --proto '=https' "$base/$asset" -o "$stage/$asset"
curl --fail --show-error --location --proto '=https' "$base/SHA256SUMS" -o "$stage/SHA256SUMS"
python3 - "$stage" "$asset" <<'PY'
import sys,pathlib,hashlib,re
stage=pathlib.Path(sys.argv[1]);asset=sys.argv[2]
rows=[line.split() for line in (stage/'SHA256SUMS').read_text().splitlines()]
values=[r[0] for r in rows if len(r)==2 and r[1]==asset]
assert len(values)==1 and re.fullmatch('[0-9a-f]{64}',values[0])
assert hashlib.sha256((stage/asset).read_bytes()).hexdigest()==values[0], 'Release checksum mismatch'
PY
mkdir "$stage/bundle"
tar -xzf "$stage/$asset" -C "$stage/bundle"
bash "$stage/bundle/install.sh" "$@"
