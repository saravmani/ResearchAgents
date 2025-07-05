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

def create_styled_sidebar():
    """Create an enhanced styled sidebar"""
    with st.sidebar:
        # Custom CSS for better sidebar styling
        st.markdown("""
        <style>
        .sidebar-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.2rem;
            border-radius: 15px;
            text-align: center;
            font-size: 1.4rem;
            font-weight: bold;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .nav-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1.2rem;
            border-radius: 12px;
            margin: 1rem 0;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        .nav-button {
            margin: 0.3rem 0;
            transition: all 0.3s ease;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        .status-online { 
            background: #28a745;
            box-shadow: 0 0 5px #28a745;
        }
        .status-offline { 
            background: #dc3545;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .metric-card {
            background: white;
            padding: 0.8rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border: 1px solid #e9ecef;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Enhanced title
        st.markdown('''
        <div class="sidebar-title">
            🤖 Research Agents
            <div style="font-size: 0.7rem; font-weight: normal; margin-top: 0.3rem; opacity: 0.9;">
                AI-Powered Platform
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        return create_navigation_section()

def create_navigation_section():
    """Create the navigation section with enhanced styling"""
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("**🧭 Navigation**")
    
    # Navigation options with descriptions
    nav_options = [
        {
            "icon": "🏠",
            "title": "Home",
            "description": "Platform overview & analytics",
            "key": "Home"
        },
        {
            "icon": "📄", 
            "title": "Document Summarizer",
            "description": "AI-powered document analysis",
            "key": "Document Summarizer"
        }
    ]
    
    # Create navigation buttons
    for option in nav_options:
        is_selected = st.session_state.current_page == option["key"]
        
        # Custom button styling based on selection
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(
            f"{option['icon']} {option['title']}",
            key=f"nav_{option['key']}",
            help=option["description"],
            use_container_width=True,
            type=button_type
        ):
            if st.session_state.current_page != option["key"]:
                st.session_state.current_page = option["key"]
                st.rerun()
        
        # Show description for selected item
        if is_selected:
            st.markdown(f'''
            <div style="
                background: #e7f3ff; 
                color: #0066cc; 
                padding: 0.4rem; 
                border-radius: 6px; 
                font-size: 0.85rem;
                margin: 0.2rem 0 0.8rem 0;
                border-left: 3px solid #0066cc;
            ">
                ✓ {option["description"]}
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Page-specific sections
    show_debug = False
    if st.session_state.current_page == "Document Summarizer":
        show_debug = create_document_tools_section()
    elif st.session_state.current_page == "Home":
        create_home_tools_section()
    
    # System status section
    create_system_status_section()
    
    # Platform info section
    create_platform_info_section()
    
    return show_debug

def create_document_tools_section():
    """Create tools section for document summarizer"""
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("**🛠️ Document Tools**")
    
    # Quick action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", help="Clear session data", use_container_width=True):
            keys_to_keep = ['current_page', 'document_graph']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.success("✅ Session reset!")
            st.rerun()
    
    with col2:
        show_debug = st.checkbox("🐛 Debug", value=False, help="Show debug information")
    
    # Session metrics
    if st.session_state.get('processing_complete', False):
        st.markdown("**📊 Current Session**")
        
        # Create metric cards
        summary_length = len(st.session_state.get('summary_result', ''))
        if summary_length > 0:
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 0.8rem; color: #666;">Summary Length</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #333;">
                    {summary_length:,} chars
                </div>
                <div style="font-size: 0.7rem; color: #888;">
                    ~{summary_length//5} words
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Last processed file
        if 'last_processed_file' in st.session_state:
            filename = st.session_state.last_processed_file
            if len(filename) > 20:
                display_name = filename[:15] + "..." + filename[-5:]
            else:
                display_name = filename
            
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 0.8rem; color: #666;">Last Processed</div>
                <div style="font-size: 0.9rem; font-weight: bold; color: #333;">
                    📄 {display_name}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    return show_debug

def create_home_tools_section():
    """Create tools section for home page"""
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("**🚀 Quick Actions**")
    
    if st.button("📄 Start Document Analysis", use_container_width=True, type="primary"):
        st.session_state.current_page = "Document Summarizer"
        st.rerun()
    
    if st.button("📊 View Analytics", use_container_width=True, disabled=True):
        st.info("🔜 Coming soon!")
    
    if st.button("⚙️ Settings", use_container_width=True, disabled=True):
        st.info("🔜 Coming soon!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_system_status_section():
    """Create system status section"""
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("**⚡ System Status**")
    
    # Status items with indicators
    status_items = [
        ("Document Parser", True),
        ("AI Summarizer", True), 
        ("Vector Database", True),
        ("API Gateway", True)
    ]
    
    for service, is_online in status_items:
        status_class = "status-online" if is_online else "status-offline"
        status_text = "Online" if is_online else "Offline"
        
        st.markdown(f'''
        <div style="
            display: flex; 
            align-items: center; 
            margin: 0.4rem 0;
            padding: 0.3rem;
            background: white;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        ">
            <span class="status-indicator {status_class}"></span>
            <span style="font-size: 0.85rem; font-weight: 500;">
                {service}
            </span>
            <span style="margin-left: auto; font-size: 0.75rem; color: #666;">
                {status_text}
            </span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_platform_info_section():
    """Create platform information section"""
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("**ℹ️ Platform Info**")
    
    info_items = [
        ("Version", "1.0.0", "🏷️"),
        ("Environment", "Production", "🌍"),
        ("Uptime", "99.9%", "⏱️"),
        ("Region", "US-East", "🌐")
    ]
    
    for label, value, icon in info_items:
        st.markdown(f'''
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            margin: 0.2rem 0;
            padding: 0.2rem 0;
            font-size: 0.8rem;
        ">
            <span style="color: #666;">
                {icon} {label}
            </span>
            <span style="font-weight: bold; color: #333;">
                {value}
            </span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main Streamlit application with enhanced navigation"""
    
    # Create the enhanced sidebar
    show_debug = create_styled_sidebar()
    
    # Display the selected page
    if st.session_state.current_page == "Home":
        show_home_page()
    elif st.session_state.current_page == "Document Summarizer":
        show_document_summarizer()
        
        # Enhanced debug section
        if show_debug:
            with st.expander("🔧 Advanced Debug Console", expanded=False):
                debug_col1, debug_col2 = st.columns(2)
                
                with debug_col1:
                    st.markdown("**📊 Session Overview**")
                    debug_data = {
                        "processing_complete": st.session_state.get("processing_complete", False),
                        "summary_length": len(st.session_state.get("summary_result", "")),
                        "current_page": st.session_state.current_page,
                        "session_keys": len(st.session_state.keys()),
                        "last_file": st.session_state.get("last_processed_file", "None"),
                        "graph_ready": 'document_graph' in st.session_state
                    }
                    st.json(debug_data)
                
                with debug_col2:
                    st.markdown("**🔧 System Info**")
                    if 'document_graph' in st.session_state:
                        st.success("✅ Document graph initialized")
                    else:
                        st.error("❌ Document graph missing")
                    
                    st.code(f"Streamlit: {st.__version__}\nWorkdir: {os.getcwd()}")
                
                # Debug console
                st.markdown("**💻 Interactive Console**")
                debug_code = st.text_area(
                    "Python code:",
                    placeholder="# Example:\n# st.metric('Keys', len(st.session_state.keys()))\n# st.write(f'Page: {st.session_state.current_page}')",
                    height=100
                )
                
                if st.button("▶️ Execute", type="primary") and debug_code.strip():
                    try:
                        exec(debug_code)
                        st.success("✅ Executed successfully!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    # Enhanced footer
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns([3, 2, 1])
    
    with footer_col1:
        st.markdown("🤖 **Powered by LangGraph & AI** | Built with Streamlit")
    
    with footer_col2:
        st.markdown(f"**Current:** {st.session_state.current_page}")
    
    with footer_col3:
        if st.button("🌙"):
            st.balloons()

if __name__ == "__main__":
    main()
