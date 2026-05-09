#!/bin/sh

set -eu

cd "$(dirname "$0")/.."
exec "${UV_BIN:-/home/ygrenzinger/.local/bin/uv}" run --frozen fetch-daily-data
