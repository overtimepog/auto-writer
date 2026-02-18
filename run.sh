#!/usr/bin/env bash
set -e

# Resolve the directory containing this script so all paths are stable
# regardless of the working directory from which the script is invoked.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
HASH_MARKER="$VENV_DIR/.requirements_hash"
MAIN="$SCRIPT_DIR/src/main.py"

# ---------------------------------------------------------------------------
# 1. Find a suitable Python (3.9+)
# ---------------------------------------------------------------------------
find_python() {
    for candidate in python3 python; do
        if command -v "$candidate" &>/dev/null; then
            # Extract major.minor and compare against 3.9
            version=$("$candidate" -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>/dev/null) || continue
            major="${version%%.*}"
            minor="${version##*.}"
            if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 9 ]; }; then
                echo "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python) || {
    echo "Error: Python 3.9+ is required but was not found." >&2
    echo "Install Python 3.9 or newer and ensure it is on your PATH." >&2
    exit 1
}
echo "Using Python: $PYTHON ($("$PYTHON" --version))"

# ---------------------------------------------------------------------------
# 2. Create virtual environment if it does not exist
# ---------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# 3. Install / update dependencies only when requirements.txt has changed
# ---------------------------------------------------------------------------

# Compute a hash of requirements.txt in a cross-platform way.
# macOS ships 'md5', Linux ships 'md5sum'.
compute_hash() {
    if command -v md5sum &>/dev/null; then
        md5sum "$1" | awk '{print $1}'
    elif command -v md5 &>/dev/null; then
        md5 -q "$1"
    else
        echo "Error: Neither 'md5sum' nor 'md5' is available." >&2
        exit 1
    fi
}

if [ -f "$REQUIREMENTS" ]; then
    CURRENT_HASH=$(compute_hash "$REQUIREMENTS")

    if [ ! -f "$HASH_MARKER" ] || [ "$(cat "$HASH_MARKER")" != "$CURRENT_HASH" ]; then
        echo "Installing dependencies from requirements.txt ..."
        "$VENV_DIR/bin/pip" install --quiet --upgrade pip
        "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS"
        # Store the hash so we can skip installation on the next run
        echo "$CURRENT_HASH" > "$HASH_MARKER"
        echo "Dependencies installed."
    else
        echo "Dependencies are up to date (requirements.txt unchanged)."
    fi
else
    echo "Warning: requirements.txt not found, skipping dependency installation." >&2
fi

# ---------------------------------------------------------------------------
# 4. Activate the venv and launch the application
# ---------------------------------------------------------------------------
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Starting autowriter ..."
exec python "$MAIN"
