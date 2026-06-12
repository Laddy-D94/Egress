import os
import subprocess
import sys
import time

# Ensure we run from the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Building Egress standalone executable...")

# Ensure tzdata is installed (for timezone support and to silence hidden import warning)
try:
    import tzdata
except ImportError:
    print("Installing tzdata for timezone data...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tzdata"])

try:
    import PyInstaller
except ImportError:
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

# tiktoken encoding plugins (cl100k_base etc.) are required by litellm for xAI/OpenAI calls
try:
    import tiktoken_ext.openai_public  # noqa: F401
except ImportError:
    print("Installing tiktoken for LLM token counting...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken"])

def kill_egress_processes() -> None:
    """Stop stray Egress.exe instances (common after testing the portable build)."""
    subprocess.call(
        ["taskkill", "/F", "/IM", "Egress.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def try_remove_file(path: str, *, attempts: int = 8, pause_s: float = 1.0) -> bool:
    if not os.path.exists(path):
        return True
    for attempt in range(1, attempts + 1):
        kill_egress_processes()
        time.sleep(pause_s)
        try:
            os.remove(path)
            return True
        except PermissionError:
            print(f"  ...still locked ({attempt}/{attempts}) — close Egress windows if any are open")
        except Exception as exc:
            print(f"  ...remove failed: {exc}")
    return False


dist_exe = os.path.join("dist", "Egress.exe")
dist_exe_new = os.path.join("dist", "Egress_new.exe")

print("Checking for running Egress.exe processes...")
kill_egress_processes()
time.sleep(1)

build_name = "Egress"
if os.path.exists(dist_exe) and not try_remove_file(dist_exe):
    print("WARNING: dist\\Egress.exe is locked. Building as Egress_new.exe, then swapping.")
    try_remove_file(dist_exe_new)
    build_name = "Egress_new"

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--clean",
    "--onefile",
    "--name", build_name,
    "--add-data", "egress.css;.",
    "--console",
    # Collect all of litellm (including its JSON data files like model_prices_and_context_window_backup.json)
    # This is required because litellm loads data files at import time.
    "--collect-all", "litellm",
    # tiktoken + plugins: without these, xAI/OpenAI calls fail with "Unknown encoding cl100k_base"
    "--collect-all", "tiktoken",
    "--collect-all", "tiktoken_ext",
    # Textual + Rich need collect-all (hidden-import alone misses subpackages/data files)
    "--collect-all", "textual",
    "--collect-all", "rich",
    "--collect-all", "edge_tts",
    "--collect-all", "pygame",
    # Essential hidden imports for Textual + Rich + our deps
    "--hidden-import", "textual",
    "--hidden-import", "rich",
    "--hidden-import", "platformdirs",
    "--hidden-import", "tzdata",  # silences "Hidden import tzdata not found" warning and ensures timezone data
    "--hidden-import", "tiktoken",
    "--hidden-import", "tiktoken_ext.openai_public",
    "--hidden-import", "requests",
    # Additional for litellm providers if --collect-all isn't enough in future
    "--hidden-import", "litellm.llms.openai",
    "--hidden-import", "litellm.llms.xai",
    "--hidden-import", "litellm.llms.ollama",
    # Sometimes needed for dynamic loading
    "--hidden-import", "importlib.metadata",
    "--hidden-import", "pkg_resources",
    # Exclude litellm's heavy proxy/UI parts (they pull fastapi etc. which we don't need)
    # This reduces warnings and exe size
    "--exclude-module", "litellm.proxy",
    "--exclude-module", "litellm.proxy.ui_crud_endpoints",
    "egress.py"
]

print("Running PyInstaller...")
subprocess.check_call(cmd)

built_exe = os.path.join("dist", f"{build_name}.exe")
if build_name != "Egress":
    if try_remove_file(dist_exe):
        os.replace(built_exe, dist_exe)
        print("Replaced locked Egress.exe with the new build.")
    else:
        print("")
        print("Build succeeded as dist\\Egress_new.exe")
        print("Could not overwrite dist\\Egress.exe (still locked).")
        print("Close ALL Egress windows, then either:")
        print("  - Delete dist\\Egress.exe manually and rename Egress_new.exe -> Egress.exe")
        print("  - Or re-run build.bat")
        sys.exit(0)

print("")
print("Build complete!")
print("Portable exe is at: dist\\Egress.exe")

# Portable launcher for dist/ (must NOT copy the source run-egress.bat — that expects a venv)
with open("dist/run-egress.bat", "w", encoding="utf-8") as f:
    f.write("""@echo off
cd /d "%~dp0"

REM Portable launcher — runs Egress.exe only. No Python/venv in this folder.
if not exist "Egress.exe" (
    echo Egress.exe not found in:
    echo   %~dp0
    echo.
    pause
    exit /b 1
)

echo Launching Egress.exe ...
echo (To play from source instead: cd ..  then  .\\run-egress.ps1)
echo.
Egress.exe
set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE% NEQ 0 (
    echo Egress.exe exited with error code %EXITCODE%.
    echo.
    echo Do NOT create a venv inside dist\\ — there is no requirements.txt here.
    echo Rebuild: cd ..  then  .\\build.bat
    echo Or run from source: cd ..  then  .\\run-egress.ps1
    echo.
)
echo Press any key to close this window...
pause >nul
exit /b %EXITCODE%
""")

with open("dist/README.txt", "w", encoding="utf-8") as f:
    f.write("""Egress - First Descent (Portable Windows Build)

Just run Egress.exe (or double-click run-egress.bat for a wrapper that keeps the console open on errors).

No Python installation required on this machine.

=== Getting started ===
1. Run the exe.
2. Go to Settings (or the app will prompt).
3. Options for playing:
   - Real LLM (recommended for best text quality): Enter your own xAI API key (get one free at console.x.ai). Model: xai/grok-3-mini-beta or xai/grok-3.
   - Local / free: Install Ollama (https://ollama.com), run "ollama pull llama3.2:3b", then in Settings set Model to "ollama/llama3.2:3b" with blank API key.
   - Pure offline (no install, no internet after download): Leave everything blank or check the "Force offline simulator" box. The game still works with all mechanics and a built-in simulator.

Your progress (characters, sessions, settings) is saved in your normal Windows user data folder (not next to this exe), so each person gets their own saves.

First launch may take a few extra seconds while it unpacks.

Enjoy your first day in the body.
""")

print("Also copied run-egress.bat and created dist\\README.txt with instructions for your friend.")
print("You can zip the entire dist\\ folder and send it, or just the Egress.exe + README.txt.")
print("No Python needed on the target machine.")
print("First run will extract files (slightly slower).")
