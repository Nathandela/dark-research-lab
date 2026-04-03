#!/usr/bin/env bash
set -euo pipefail

# Cross-compile drl Go binary for all target platforms.
# Output: go/dist/drl-{os}-{arch}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
GO_DIR="$REPO_ROOT/go"
DIST_DIR="$GO_DIR/dist"

PLATFORMS=(
    "darwin/arm64"
    "darwin/amd64"
    "linux/arm64"
    "linux/amd64"
    "windows/amd64"
    "windows/arm64"
)

VERSION="${VERSION:-$(cd "$GO_DIR" && git describe --tags --always --dirty 2>/dev/null || echo "dev")}"
COMMIT="${COMMIT:-$(cd "$GO_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")}"
LDFLAGS="-s -w -X github.com/nathandelacretaz/dark-research-lab/internal/build.Version=$VERSION -X github.com/nathandelacretaz/dark-research-lab/internal/build.Commit=$COMMIT"

mkdir -p "$DIST_DIR"

echo "Building drl v${VERSION} (${COMMIT})"

for platform in "${PLATFORMS[@]}"; do
    IFS='/' read -r os arch <<< "$platform"
    output="$DIST_DIR/drl-${os}-${arch}"
    if [ "$os" = "windows" ]; then
        output="${output}.exe"
    fi
    echo "  -> $output"
    (cd "$GO_DIR" && GOOS="$os" GOARCH="$arch" go build -ldflags "$LDFLAGS" -o "$output" ./cmd/drl/)
done

echo "Done. Binaries in $DIST_DIR/"
ls -la "$DIST_DIR/"
