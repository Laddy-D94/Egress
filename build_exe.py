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

# Try to remove old exe if it exists (common cause of permission errors on Windows if it was running)
dist_exe = os.path.join("dist", "Egress.exe")
if os.path.exists(dist_exe):
    print("Attempting to remove previous Egress.exe (close any running Egress windows!)...")
    try:
        # Try to kill any running Egress.exe processes first
        subprocess.call(['taskkill', '/F', '/IM', 'Egress.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)  # brief pause for OS to release the file
        os.remove(dist_exe)
        print("Previous Egress.exe removed successfully.")
    except PermissionError:
        print("WARNING: Could not remove old Egress.exe (file may still be in use by another process or antivirus). Close all Egress windows, wait a few seconds, and try the build again.")
    except FileNotFoundError:
        pass  # taskkill not found or no process
    except Exception as e:
        print(f"WARNING: Unexpected issue cleaning old exe: {e}")

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--clean",
    "--onefile",
    "--name", "Egress",
    "--add-data", "egress.css;.",
    "--console",
    # Collect all of litellm (including its JSON data files like model_prices_and_context_window_backup.json)
    # This is required because litellm loads data files at import time.
    "--collect-all", "litellm",
    # tiktoken + plugins: without these, xAI/OpenAI calls fail with "Unknown encoding cl100k_base"
    "--collect-all", "tiktoken",
    "--collect-all", "tiktoken_ext",
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

print("")
print("Build complete!")
print("Portable exe is at: dist\\Egress.exe")

# Copy convenience launcher and create simple instructions for recipients
import shutil
if os.path.exists("run-egress.bat"):
    shutil.copy("run-egress.bat", "dist/run-egress.bat")

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
