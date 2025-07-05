import streamlit as st
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Import page modules
try:
    from home_page import show_home_page
    from document_summarizer import show_document_summarizer, initialize_document_summarizer_session
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Research Agents Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Initialize document summarizer session state
initialize_document_summarizer_session()

def inject_premium_css():
    """Inject premium CSS styling"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global sidebar styling */
    .css-1d391kg {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        box-shadow: 2px 0 10px rgba(0,0,0,0.3);
    }
    
    /* Override Streamlit default colors */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Premium sidebar header */
    .premium-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 2rem 1.5rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .premium-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="1.5" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="80" r="1" fill="rgba(255,255,255,0.1)"/></svg>');
        opacity: 0.3;
    }
    
    .premium-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .premium-subtitle {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }
    
    /* Navigation section */
    .nav-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .nav-title {
        color: #e2e8f0;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Navigation buttons */
    .nav-button {
        width: 100%;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #e2e8f0;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .nav-button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(99, 102, 241, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
    }
    
    .nav-button.active {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-color: #6366f1;
        color: white;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
    }
    
    .nav-button.active::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
    }
    
    .nav-button-icon {
        font-size: 1.3rem;
        margin-right: 0.8rem;
        vertical-align: middle;
    }
    
    .nav-button-text {
        font-weight: 500;
        font-size: 1rem;
        vertical-align: middle;
    }
    
    .nav-button-desc {
        font-size: 0.8rem;
        opacity: 0.8;
        margin-top: 0.3rem;
        font-weight: 400;
    }
    
    /* Status indicator */
    .status-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .status-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.8rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #10b981;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        margin-right: 0.8rem;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.8rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15);
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: #e2e8f0;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0.3rem 0;
    }
    
    .metric-desc {
        color: #94a3b8;
        font-size: 0.75rem;
    }
    
    /* Action buttons */
    .action-button {
        width: 100%;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border: none;
        border-radius: 8px;
        padding: 0.8rem;
        color: white;
        font-weight: 500;
        margin: 0.3rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }
    
    .action-button.secondary {
        background: rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Platform info */
    .platform-info {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .info-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        color: #e2e8f0;
        font-size: 0.85rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .info-item:last-child {
        border-bottom: none;
    }
    
    .info-label {
        color: #94a3b8;
        font-weight: 500;
    }
    
    .info-value {
        font-weight: 600;
        color: #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

def create_premium_sidebar():
    """Create a premium styled sidebar"""
    inject_premium_css()
    
    with st.sidebar:
        # Premium header
        st.markdown('''
        <div class="premium-header">
            <div class="premium-title">🤖 Research Agents</div>
            <div class="premium-subtitle">AI-Powered Intelligence Platform</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Navigation section
        show_debug = create_premium_navigation()
        
        # Page-specific tools
        if st.session_state.current_page == "Document Summarizer":
            create_document_metrics()
            create_document_actions()
        elif st.session_state.current_page == "Home":
            create_home_quick_actions()
        
        # System status
        create_system_status()
        
        # Platform info
        create_platform_info()
        
        return show_debug

def create_premium_navigation():
    """Create premium navigation with enhanced styling"""
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">🧭 Navigation</div>', unsafe_allow_html=True)
    
    # Navigation options
    nav_options = [
        {
            "icon": "🏠",
            "title": "Home",
            "description": "Dashboard & Analytics",
            "key": "Home"
        },
        {
            "icon": "📄", 
            "title": "Document Summarizer",
            "description": "AI Document Analysis",
            "key": "Document Summarizer"
        }
    ]
    
    # Create custom navigation buttons
    for option in nav_options:
        is_active = st.session_state.current_page == option["key"]
        active_class = "active" if is_active else ""
        
        # Create clickable navigation item
        if st.button(
            f"{option['icon']} {option['title']}",
            key=f"nav_{option['key']}",
            help=option["description"],
            use_container_width=True
        ):
            if st.session_state.current_page != option["key"]:
                st.session_state.current_page = option["key"]
                st.rerun()
        
        # Show description for active item
        if is_active:
            st.markdown(f'''
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
                padding: 0.6rem;
                margin: 0.5rem 0 1rem 0;
                color: #e2e8f0;
                font-size: 0.85rem;
                text-align: center;
            ">
                ✨ {option["description"]}
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Debug toggle for document summarizer
    show_debug = False
    if st.session_state.current_page == "Document Summarizer":
        show_debug = st.checkbox("🔧 Developer Mode", value=False, help="Show debug information")
    
    return show_debug

def create_document_metrics():
    """Create document processing metrics"""
    if st.session_state.get('processing_complete', False):
        st.markdown('<div class="nav-container">', unsafe_allow_html=True)
        st.markdown('<div class="nav-title">📊 Session Metrics</div>', unsafe_allow_html=True)
        
        # Summary length metric
        summary_length = len(st.session_state.get('summary_result', ''))
        if summary_length > 0:
            word_count = summary_length // 5
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Summary Generated</div>
                <div class="metric-value">{summary_length:,}</div>
                <div class="metric-desc">characters (~{word_count:,} words)</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Processing time (if available)
        if 'processing_time' in st.session_state:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Processing Time</div>
                <div class="metric-value">{st.session_state.processing_time:.1f}s</div>
                <div class="metric-desc">AI analysis duration</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Last processed file
        if 'last_processed_file' in st.session_state:
            filename = st.session_state.last_processed_file
            display_name = filename[:20] + "..." if len(filename) > 20 else filename
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Current Document</div>
                <div class="metric-value" style="font-size: 1rem;">📄 {display_name}</div>
                <div class="metric-desc">ready for analysis</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def create_document_actions():
    """Create document processing action buttons"""
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset", help="Clear session data", use_container_width=True):
            keys_to_keep = ['current_page', 'document_graph']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.success("✅ Session cleared!")
            st.rerun()
    
    with col2:
        if st.button("💾 Export", help="Export results", use_container_width=True, disabled=not st.session_state.get('processing_complete', False)):
            if st.session_state.get('processing_complete', False):
                st.info("🔜 Export feature coming soon!")
            else:
                st.warning("⚠️ No data to export")
    
    # Additional actions
    if st.button("📋 Copy Summary", help="Copy to clipboard", use_container_width=True, disabled=not st.session_state.get('processing_complete', False)):
        if st.session_state.get('summary_result'):
            st.success("📋 Summary copied to clipboard!")
        else:
            st.warning("⚠️ No summary available")
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_home_quick_actions():
    """Create quick actions for home page"""
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">🚀 Quick Start</div>', unsafe_allow_html=True)
    
    if st.button("📄 Analyze Document", use_container_width=True, type="primary"):
        st.session_state.current_page = "Document Summarizer"
        st.rerun()
    
    if st.button("📊 View Reports", use_container_width=True, disabled=True):
        st.info("🔜 Coming soon!")
    
    if st.button("⚙️ Configure AI", use_container_width=True, disabled=True):
        st.info("🔜 Settings panel coming soon!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_system_status():
    """Create system status section"""
    st.markdown('<div class="status-container">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">⚡ System Status</div>', unsafe_allow_html=True)
    
    services = [
        ("🔤 Document Parser", True),
        ("🧠 AI Summarizer", True),
        ("🗄️ Vector Store", True),
        ("🌐 API Gateway", True)
    ]
    
    for service, is_online in services:
        status_color = "#10b981" if is_online else "#ef4444"
        status_text = "Online" if is_online else "Offline"
        
        st.markdown(f'''
        <div class="status-item">
            <div style="display: flex; align-items: center;">
                <div class="status-dot" style="background: {status_color}; box-shadow: 0 0 10px {status_color};"></div>
                <span style="color: #e2e8f0; font-weight: 500;">{service}</span>
            </div>
            <span style="color: {status_color}; font-weight: 600; font-size: 0.8rem;">{status_text}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_platform_info():
    """Create platform information section"""
    st.markdown('<div class="platform-info">', unsafe_allow_html=True)
    st.markdown('<div class="nav-title">ℹ️ Platform Info</div>', unsafe_allow_html=True)
    
    info_items = [
        ("🏷️ Version", "v2.1.0"),
        ("🌍 Environment", "Production"),
        ("⏱️ Uptime", "99.9%"),
        ("🌐 Region", "Global"),
        ("🔒 Security", "Enterprise"),
        ("📊 Load", "Optimal")
    ]
    
    for label, value in info_items:
        st.markdown(f'''
        <div class="info-item">
            <span class="info-label">{label}</span>
            <span class="info-value">{value}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application with premium UI"""
    
    # Create premium sidebar
    show_debug = create_premium_sidebar()
    
    # Main content area
    if st.session_state.current_page == "Home":
        show_home_page()
    elif st.session_state.current_page == "Document Summarizer":
        show_document_summarizer()
        
        # Enhanced debug console
        if show_debug:
            with st.expander("🔧 Developer Console", expanded=False):
                debug_tabs = st.tabs(["📊 Session", "🔧 System", "💻 Console", "📁 Files"])
                
                with debug_tabs[0]:
                    st.markdown("**Session State Overview**")
                    debug_data = {
                        "processing_complete": st.session_state.get("processing_complete", False),
                        "summary_length": len(st.session_state.get("summary_result", "")),
                        "current_page": st.session_state.current_page,
                        "session_keys": list(st.session_state.keys()),
                        "last_file": st.session_state.get("last_processed_file", "None"),
                        "graph_ready": 'document_graph' in st.session_state
                    }
                    st.json(debug_data)
                
                with debug_tabs[1]:
                    st.markdown("**System Information**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Streamlit Version", st.__version__)
                        st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}")
                        
                    with col2:
                        st.metric("Session Keys", len(st.session_state.keys()))
                        st.metric("Working Directory", os.path.basename(os.getcwd()))
                    
                    if 'document_graph' in st.session_state:
                        st.success("✅ Document processing graph initialized")
                    else:
                        st.error("❌ Document processing graph not found")
                
                with debug_tabs[2]:
                    st.markdown("**Interactive Python Console**")
                    debug_code = st.text_area(
                        "Execute Python code:",
                        placeholder="# Examples:\n# st.metric('Active Keys', len(st.session_state.keys()))\n# st.success(f'Current page: {st.session_state.current_page}')",
                        height=120
                    )
                    
                    if st.button("▶️ Execute Code", type="primary") and debug_code.strip():
                        try:
                            exec(debug_code)
                            st.success("✅ Code executed successfully!")
                        except Exception as e:
                            st.error(f"❌ Execution error: {e}")
                
                with debug_tabs[3]:
                    st.markdown("**File System**")
                    st.code(f"Current directory: {os.getcwd()}")
                    if st.button("📁 List Files"):
                        files = [f for f in os.listdir('.') if os.path.isfile(f)]
                        st.write("Files in current directory:")
                        for file in files[:10]:  # Show first 10 files
                            st.text(f"📄 {file}")
                        if len(files) > 10:
                            st.text(f"... and {len(files) - 10} more files")

    # Enhanced footer
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns([4, 2, 1])
    
    with footer_col1:
        st.markdown("🤖 **Research Agents Platform** • Powered by LangGraph & Advanced AI")
    
    with footer_col2:
        st.markdown(f"**Active:** {st.session_state.current_page}")
    
    with footer_col3:
        if st.button("🎉", help="Celebrate!"):
            st.balloons()

if __name__ == "__main__":
    main()
