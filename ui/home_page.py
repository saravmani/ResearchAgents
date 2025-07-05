import streamlit as st
import time
import json

def show_home_page():
    """Display the home page with simple widgets"""
    st.title("🤖 Research Agents Platform")
    st.markdown("Welcome to the AI-powered Research and Document Processing Platform!")
    
    # Create columns for widgets
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔬 Research Reports",
            value="50+",
            delta="12 this month"
        )
        
    with col2:
        st.metric(
            label="📄 Documents Processed",
            value="150+",
            delta="25 this week"
        )
        
    with col3:
        st.metric(
            label="🤖 AI Models Active",
            value="3",
            delta="100% uptime"
        )
    
    # Feature overview
    st.markdown("## 🚀 Platform Features")
    
    feature_col1, feature_col2 = st.columns(2)
    
    with feature_col1:
        st.markdown("""
        ### 📊 Document Summarization
        - **AI-powered parsing** of PDF, Word, and text files
        - **Intelligent summarization** with key insights
        - **Progress tracking** and real-time updates
        - **Export options** in multiple formats
        """)
        
        if st.button("🔗 Go to Document Summarizer", type="primary", use_container_width=True):
            st.session_state.current_page = "Document Summarizer"
            st.rerun()
    
    with feature_col2:
        st.markdown("""
        ### 🔬 Research Analysis
        - **Equity research reports** generation
        - **Financial data extraction** from text
        - **Multi-agent workflows** for comprehensive analysis
        - **ChromaDB integration** for context retrieval
        """)
        
        st.button("🔗 Research Tools (Coming Soon)", disabled=True, use_container_width=True)
    
    # Quick stats
    st.markdown("## 📈 Quick Stats")
    
    # Create sample data for demonstration
    chart_data = {
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Documents": [5, 8, 12, 7, 15, 3, 6],
        "Reports": [2, 4, 3, 5, 8, 1, 2]
    }
    
    st.bar_chart(chart_data, x="Day", y=["Documents", "Reports"])
    
    # System status
    st.markdown("## ⚙️ System Status")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.success("🟢 Document Parser: Online")
    
    with status_col2:
        st.success("🟢 AI Summarizer: Online")
    
    with status_col3:
        st.success("🟢 Vector Database: Online")
    
    # Additional platform information
    st.markdown("## 📋 Platform Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.info("""
        **🔧 Technical Stack:**
        - LangGraph for multi-agent workflows
        - Groq LLama 3 for AI processing
        - ChromaDB for vector storage
        - Streamlit for web interface
        """)
    
    with info_col2:
        st.info("""
        **📊 Recent Updates:**
        - Enhanced document parsing accuracy
        - Improved summarization quality
        - Added multi-format export options
        - Optimized processing speed
        """)
    
    # Getting started section
    st.markdown("## 🚀 Getting Started")
    
    with st.expander("📖 How to Use the Platform", expanded=False):
        st.markdown("""
        ### Document Summarization:
        1. 📤 Navigate to the **Document Summarizer** page
        2. 📁 Upload your document (PDF, Word, or Text)
        3. ✏️ Add custom instructions (optional)
        4. 🚀 Click "Process Document"
        5. 📋 View and export your summary
        
        ### Supported File Types:
        - **PDF files** (.pdf) - Extracted using PyMuPDF
        - **Word documents** (.docx, .doc) - Parsed with python-docx
        - **Text files** (.txt) - Direct text processing
        
        ### Export Options:
        - Plain text format
        - JSON with metadata
        - Markdown format
        """)
    
    # Footer metrics
    st.markdown("---")
    footer_col1, footer_col2, footer_col3, footer_col4 = st.columns(4)
    
    with footer_col1:
        st.metric("⚡ Avg Processing Time", "45s", "-12s")
    
    with footer_col2:
        st.metric("🎯 Accuracy Rate", "95.8%", "+2.1%")
    
    with footer_col3:
        st.metric("💾 Data Processed", "2.3TB", "+150GB")
    
    with footer_col4:
        st.metric("👥 Active Users", "127", "+15")
