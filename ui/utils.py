"""
UI utilities and helper functions for the Research Agents Platform
"""

import streamlit as st
import time
from typing import Dict, Any, Optional

def show_success_message(message: str, duration: int = 3):
    """Display a success message that auto-dismisses"""
    success_placeholder = st.empty()
    success_placeholder.success(message)
    time.sleep(duration)
    success_placeholder.empty()

def show_error_message(message: str, duration: int = 5):
    """Display an error message that auto-dismisses"""
    error_placeholder = st.empty()
    error_placeholder.error(message)
    time.sleep(duration)
    error_placeholder.empty()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_processing_status_emoji(stage: str) -> str:
    """Get emoji for processing stage"""
    status_emojis = {
        "initialized": "🔄",
        "parsing": "📖",
        "parsed": "✅",
        "summarizing": "🤖",
        "completed": "🎉",
        "error": "❌",
        "parse_error": "⚠️",
        "summary_error": "⚠️"
    }
    return status_emojis.get(stage, "🔄")

def create_download_filename(original_name: str, suffix: str, extension: str) -> str:
    """Create a download filename with timestamp"""
    import os
    from datetime import datetime
    
    # Remove original extension
    base_name = os.path.splitext(original_name)[0]
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{base_name}_{suffix}_{timestamp}.{extension}"

def display_session_metrics():
    """Display session metrics in sidebar"""
    if 'session_metrics' not in st.session_state:
        st.session_state.session_metrics = {
            'documents_processed': 0,
            'total_processing_time': 0,
            'session_start_time': time.time()
        }
    
    metrics = st.session_state.session_metrics
    session_duration = time.time() - metrics['session_start_time']
    
    st.sidebar.markdown("### 📊 Session Metrics")
    st.sidebar.metric("Documents Processed", metrics['documents_processed'])
    st.sidebar.metric("Session Duration", f"{session_duration/60:.1f} min")
    
    if metrics['documents_processed'] > 0:
        avg_time = metrics['total_processing_time'] / metrics['documents_processed']
        st.sidebar.metric("Avg Processing Time", f"{avg_time:.1f}s")

def update_session_metrics(processing_time: float):
    """Update session metrics after document processing"""
    if 'session_metrics' not in st.session_state:
        st.session_state.session_metrics = {
            'documents_processed': 0,
            'total_processing_time': 0,
            'session_start_time': time.time()
        }
    
    st.session_state.session_metrics['documents_processed'] += 1
    st.session_state.session_metrics['total_processing_time'] += processing_time

def create_info_card(title: str, content: str, icon: str = "ℹ️") -> None:
    """Create a styled info card"""
    st.markdown(f"""
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: #1f77b4;">
            {icon} {title}
        </h4>
        <p style="margin: 0; color: #333;">
            {content}
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_feature_card(title: str, description: str, icon: str, button_text: str, 
                     button_action: Optional[callable] = None, disabled: bool = False):
    """Display a feature card with button"""
    with st.container():
        st.markdown(f"### {icon} {title}")
        st.markdown(description)
        
        if button_action and not disabled:
            if st.button(button_text, type="primary", use_container_width=True):
                button_action()
        else:
            st.button(button_text, disabled=disabled, use_container_width=True)

def safe_session_state_access(key: str, default: Any = None) -> Any:
    """Safely access session state with default value"""
    return st.session_state.get(key, default)

def reset_processing_state():
    """Reset processing-related session state"""
    keys_to_reset = [
        'processing_complete',
        'summary_result',
        'last_processed_file',
        'processing_start_time'
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

def display_debug_info(show_full: bool = False):
    """Display debug information"""
    if show_full:
        st.json(dict(st.session_state))
    else:
        debug_data = {
            "current_page": st.session_state.get("current_page", "Unknown"),
            "processing_complete": st.session_state.get("processing_complete", False),
            "session_keys_count": len(st.session_state.keys()),
            "has_document_graph": 'document_graph' in st.session_state
        }
        st.json(debug_data)

def get_page_config() -> Dict[str, Any]:
    """Get default page configuration"""
    return {
        "page_title": "Research Agents Platform",
        "page_icon": "🤖",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
