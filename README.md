# Human Auto Typer (HAT)

A desktop application for macOS and Windows that reads your clipboard and types it out with human-like behavior. Copy text, press a global hotkey, and watch it get typed naturally into any focused application — complete with realistic delays and occasional typos.

## Features

- **Global Hotkey** — Press `Cmd+Shift+K` (macOS) or `Ctrl+Shift+K` (Windows) from any app to start typing your clipboard contents
- **Human-Like Typing** — Gaussian-distributed keystroke delays that mimic real typing patterns
- **Realistic Typos** — Optional adjacent-key typos with automatic backspace correction
- **Instant Cancel** — Press `Escape` to stop typing immediately
- **Modern GUI** — Dark-themed settings panel with live status indicator
- **Fully Configurable** — Adjust typing speed (30–120 WPM), typo rate (0–10%), and hotkey bindings
- **Persistent Settings** — Your preferences are saved between sessions

## Requirements

- macOS 13+ (Ventura or later) **or** Windows 10+
- Python 3.11 or 3.13
- **macOS:** Accessibility permissions (the app will guide you through setup)
- **macOS:** tkinter (`brew install python-tk@3.13` if using Homebrew Python)
- **Windows:** No special permissions required

## Installation & Usage

```bash
# Clone the repository
git clone https://github.com/overtimepog/Human-Auto-Typer
cd Human-Auto-Typer
```

The included launcher scripts handle everything automatically — they find the right Python version, create a virtual environment, install dependencies (only when needed), and start the app.

**macOS / Linux:**

```bash
./run.sh
```

**Windows:**

```bat
run.bat
```

**Manual launch** (if you prefer to manage your own environment):

```bash
pip install -r requirements.txt
python3 src/main.py
```

### Quick Start

1. Launch the app — the GUI window will appear
2. **macOS only:** Grant Accessibility permissions when prompted (System Settings > Privacy & Security > Accessibility)
3. Copy any text to your clipboard
4. Switch to the app where you want the text typed
5. Press **Cmd+Shift+K** (macOS) or **Ctrl+Shift+K** (Windows) — the text types out naturally
6. Press **Escape** at any time to cancel

### Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Typing Speed | 30–120 WPM | 70 WPM | How fast characters are typed |
| Typo Rate | 0–10% | 1.5% | Chance of hitting an adjacent key |
| Activate Hotkey | Any combo | `Cmd+Shift+K` / `Ctrl+Shift+K` | Triggers typing |
| Cancel Hotkey | Any combo | `Escape` | Stops typing immediately |

Settings are persisted to `~/.config/autotyper/settings.json`.

### Hotkey Format

Hotkeys use [pynput key notation](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key):

```
<cmd>+<shift>+k       # Command + Shift + K
<ctrl>+<alt>+t        # Control + Alt + T
<esc>                  # Escape
```

## How It Works

### Typing Simulation

The typing engine simulates human behavior through several mechanisms:

- **Gaussian delays** — Inter-keystroke timing follows a normal distribution rather than fixed intervals. At 70 WPM, the mean delay is ~171ms with natural variance.
- **Adjacent-key typos** — When a typo triggers, the engine types a neighboring key on the QWERTY layout, pauses briefly, backspaces, then types the correct character.
- **Special character handling** — Newlines press Enter, tabs press Tab, and Unicode characters are handled natively through OS input services.

### Architecture

```
src/
├── main.py                  # Entry point
├── app_controller.py        # Orchestrator — wires all modules together
├── platform_support.py      # Platform-aware constants (hotkeys, fonts)
├── gui/
│   ├── main_window.py       # Status display, hotkey hint, window chrome
│   └── settings_panel.py    # Speed/typo sliders, hotkey entries
├── engine/
│   ├── typing_engine.py     # Core typing loop with cancel support
│   ├── delay_model.py       # Gaussian delay calculation
│   └── typo_generator.py    # QWERTY adjacency map and typo logic
├── hotkey/
│   └── hotkey_listener.py   # Persistent pynput listener with swappable hotkeys
├── clipboard/
│   └── clipboard_reader.py  # Pyperclip wrapper with error handling
├── config/
│   └── config_store.py      # JSON settings with atomic writes
└── permissions/
    └── accessibility.py     # Platform-aware permission helper
```

**Threading model:**

| Thread | Role |
|--------|------|
| Main | Tk GUI event loop |
| Hotkey listener | pynput keyboard listener (daemon) |
| Typing worker | Keystroke injection (one at a time, lock-guarded) |

## Platform Notes

### macOS — Accessibility Permissions

AutoTyper needs Accessibility permissions to register global hotkeys and simulate keystrokes. On first launch:

1. macOS will prompt you to grant permissions
2. Go to **System Settings → Privacy & Security → Accessibility**
3. Add your **terminal app** (Terminal, iTerm2, etc.) to the allowed list
4. Restart AutoTyper

> **Note:** When running from the terminal, permissions are granted to the terminal app itself, not to Python. If you bundle AutoTyper as a `.app`, the bundle gets its own permission entry.

### Windows

No special permissions are required. AutoTyper uses standard Windows input hooks via pynput. If you encounter issues registering hotkeys, try running the application as Administrator.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

### Project Dependencies

| Library | Purpose |
|---------|---------|
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern themed GUI framework |
| [pynput](https://github.com/moses-palmer/pynput) | Keyboard monitoring and simulation |
| [pyperclip](https://github.com/asweigart/pyperclip) | Cross-platform clipboard access |

## License

MIT
