"""
Debug utility for monitoring the Streamlit Document Summarizer app
This script helps with debugging and monitoring the running application.
"""

import sys
import os
import time
import requests
import json
from typing import Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StreamlitDebugger:
    """Debug utility for the Streamlit app"""
    
    def __init__(self, streamlit_url: str = "http://localhost:8502"):
        self.streamlit_url = streamlit_url
        
    def check_app_status(self) -> bool:
        """Check if the Streamlit app is running"""
        try:
            response = requests.get(f"{self.streamlit_url}/healthz", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def monitor_app(self, interval: int = 30):
        """Monitor the app status periodically"""
        print(f"🔍 Starting Streamlit app monitoring...")
        print(f"📍 URL: {self.streamlit_url}")
        print(f"⏰ Check interval: {interval} seconds")
        print("-" * 50)
        
        while True:
            try:
                status = "🟢 ONLINE" if self.check_app_status() else "🔴 OFFLINE"
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] App Status: {status}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(interval)
    
    def test_document_graph(self):
        """Test the document processing graph"""
        print("🧪 Testing document processing graph...")
        
        try:
            from graphs.documentsummarygraph import create_document_summary_graph
            
            # Create graph
            graph = create_document_summary_graph()
            print("✅ Document graph created successfully")
            
            # Test with sample data
            sample_text = "This is a test document for debugging purposes."
            config = {"configurable": {"thread_id": "debug_test"}}
            
            print("🔄 Running test processing...")
            
            for state in graph.stream(
                {
                    "messages": [("user", "Create a brief summary")],
                    "file_content": sample_text.encode('utf-8'),
                    "file_name": "debug_test.txt",
                    "file_type": "txt"
                }, 
                config,
                stream_mode="values"
            ):
                stage = state.get("processing_stage", "unknown")
                print(f"  📋 Stage: {stage}")
                
                if stage == "completed":
                    print("✅ Test completed successfully")
                    break
                elif "error" in stage:
                    error = state.get("error_message", "Unknown error")
                    print(f"❌ Test failed: {error}")
                    break
            
        except Exception as e:
            print(f"❌ Graph test failed: {e}")
    
    def show_debug_info(self):
        """Show debugging information"""
        print("🔧 Debug Information")
        print("=" * 50)
        
        # Python environment
        print(f"🐍 Python Version: {sys.version}")
        print(f"📁 Working Directory: {os.getcwd()}")
        print(f"📦 Python Path: {sys.path[:3]}...")
        
        # Check dependencies
        dependencies = [
            "streamlit", "langgraph", "langchain", "fitz", "docx"
        ]
        
        print("\n📚 Dependencies:")
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"  ✅ {dep}: Available")
            except ImportError:
                print(f"  ❌ {dep}: Missing")
        
        # Check graph functionality
        print("\n🔗 Graph Status:")
        try:
            from graphs.documentsummarygraph import create_document_summary_graph
            graph = create_document_summary_graph()
            print("  ✅ Document Summary Graph: OK")
        except Exception as e:
            print(f"  ❌ Document Summary Graph: Error - {e}")
        
        # App status
        print(f"\n🌐 App Status:")
        if self.check_app_status():
            print(f"  ✅ Streamlit App: Running at {self.streamlit_url}")
        else:
            print(f"  ❌ Streamlit App: Not accessible at {self.streamlit_url}")

def main():
    """Main debug utility function"""
    debugger = StreamlitDebugger()
    
    print("🤖 Streamlit Document Summarizer - Debug Utility")
    print("=" * 60)
    
    while True:
        print("\nSelect an option:")
        print("1. 📊 Show debug information")
        print("2. 🔍 Monitor app status")
        print("3. 🧪 Test document graph")
        print("4. 🌐 Check app accessibility")
        print("5. 🚪 Exit")
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                debugger.show_debug_info()
            
            elif choice == "2":
                try:
                    interval = int(input("Enter monitoring interval in seconds (default 30): ") or "30")
                    debugger.monitor_app(interval)
                except ValueError:
                    print("❌ Invalid interval. Using default 30 seconds.")
                    debugger.monitor_app(30)
            
            elif choice == "3":
                debugger.test_document_graph()
            
            elif choice == "4":
                status = "🟢 ACCESSIBLE" if debugger.check_app_status() else "🔴 NOT ACCESSIBLE"
                print(f"App status: {status}")
                if debugger.check_app_status():
                    print(f"🔗 Open in browser: {debugger.streamlit_url}")
            
            elif choice == "5":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
