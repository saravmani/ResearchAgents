"""
Simple runner script for the human loop UI.
Run this to start the Streamlit UI.
"""
import subprocess
import sys
import os

def run_ui():
    """Run the human loop simple UI."""
    ui_file = os.path.join("ui", "human_loop_simple_ui.py")
    
    if not os.path.exists(ui_file):
        print(f"❌ UI file not found: {ui_file}")
        return
    
    print("🚀 Starting Human Loop Simple UI...")
    print(f"📁 Running: {ui_file}")
    print("🌐 Opening browser at: http://localhost:8501")
    print("\n" + "="*50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", ui_file,
            "--server.port", "8501",
            "--server.headless", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running UI: {e}")

if __name__ == "__main__":
    run_ui()