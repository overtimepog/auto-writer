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
# 1. Find the newest Python 3 installation
# ---------------------------------------------------------------------------
find_python() {
    local best_cmd=""
    local best_major=0
    local best_minor=0

    for candidate in python3.13 python3.11; do
        if command -v "$candidate" &>/dev/null; then
            version=$("$candidate" -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>/dev/null) || continue
            major="${version%%.*}"
            minor="${version##*.}"
            # Only consider Python 3+
            [ "$major" -lt 3 ] && continue
            # Keep this candidate if it's newer than our current best
            if [ "$major" -gt "$best_major" ] || { [ "$major" -eq "$best_major" ] && [ "$minor" -gt "$best_minor" ]; }; then
                best_major="$major"
                best_minor="$minor"
                best_cmd="$candidate"
            fi
        fi
    done

    if [ -n "$best_cmd" ]; then
        echo "$best_cmd"
        return 0
    fi
    return 1
}

PYTHON=$(find_python) || {
    echo "Error: Python 3.11 or 3.13 is required but was not found." >&2
    echo "Install Python 3.11 or 3.13 and ensure it is on your PATH." >&2
    exit 1
}
echo "Using Python: $PYTHON ($("$PYTHON" --version))"

# ---------------------------------------------------------------------------
# 2. Verify tkinter is available (required for GUI)
# ---------------------------------------------------------------------------
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
    echo "Error: tkinter is not available for $PYTHON." >&2
    if command -v brew &>/dev/null; then
        PY_VER=$("$PYTHON" -c "import sys; print('%d.%d' % sys.version_info[:2])")
        echo "Install it with: brew install python-tk@$PY_VER" >&2
    else
        echo "Install the tkinter package for your Python version." >&2
    fi
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. Create virtual environment if it does not exist
# ---------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# 4. Install / update dependencies only when requirements.txt has changed
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
        "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
        "$VENV_DIR/bin/python" -m pip install -r "$REQUIREMENTS"
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
# 5. Activate the venv and launch the application
# ---------------------------------------------------------------------------
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Starting autowriter ..."
exec python "$MAIN"
