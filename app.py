import streamlit as st
import re
import json
from datetime import timedelta
from youtube_transcript_api import YouTubeTranscriptApi
import anthropic
from typing import List, Dict, Optional, Tuple
import time


# Default prompts for each phase
DEFAULT_PROMPTS = {
    "classification": """Analyze this transcript and classify it into one of these categories:
- Tutorial/Educational: Step-by-step instructions or educational content
- Interview/Conversation: Dialogue between multiple people
- Presentation/Talk: Single speaker presenting ideas
- News/Documentary: Factual reporting or documentary content
- Entertainment/Story: Narrative or entertainment content
- Review/Analysis: Product reviews or analytical content

Provide the classification and a brief reason for your choice.""",
    
    "extraction": """Find and extract the following elements from this transcript:
- Key Ideas: Main concepts and themes
- Introductions: How topics are introduced
- Substantiations: Evidence, data, or support for claims
- Analogies: Comparisons and metaphors used
- Insights: Unique perspectives or realizations
- Examples: Concrete examples provided

Format as structured data.""",
    
    "writing": """Based on the extracted elements, write an article following these principles:
- Minimize words, maximize clarity
- Imply don't explain
- Facts over commentary
- Clear structure with headings
- Engaging but concise"""
}


class YouTubeTranscriptExtractor:
    def __init__(self):
        pass
    
    def extract_video_id(self, url: str) -> Optional[str]:
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/.*[?&]v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def format_timestamp(self, seconds: float) -> str:
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_transcript_with_timestamps(self, video_id: str) -> Tuple[str, List[Dict], str]:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            formatted_transcript = ""
            structured_transcript = []
            plain_text = ""
            
            for entry in transcript_list:
                timestamp = self.format_timestamp(entry['start'])
                text = entry['text'].strip()
                
                formatted_transcript += f"[{timestamp}] {text}\n"
                plain_text += f"{text} "
                structured_transcript.append({
                    'timestamp': timestamp,
                    'start_seconds': entry['start'],
                    'text': text
                })
            
            return formatted_transcript, structured_transcript, plain_text.strip()
        except Exception as e:
            return f"Error: {str(e)}", [], ""


class EnhancedArticleGenerator:
    def __init__(self, api_key: str):
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.api_key_valid = True
        except Exception as e:
            self.api_key_valid = False
            self.error_message = str(e)
    
    def validate_api_key(self) -> Tuple[bool, str]:
        if not self.api_key_valid:
            return False, f"API key validation failed: {self.error_message}"
        return True, "API key is valid"
    
    def classify_content(self, transcript: str, classification_prompt: str, progress_callback=None) -> Dict:
        """Phase 1: Classify the content type"""
        try:
            if progress_callback:
                progress_callback("🔍 Phase 1/3: Classifying content type...")
            
            prompt = f"{classification_prompt}\n\nTranscript:\n{transcript[:5000]}"  # Limit for classification
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            classification_result = message.content[0].text
            
            if progress_callback:
                progress_callback("✅ Classification complete!")
            
            return {
                "success": True,
                "classification": classification_result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_elements(self, transcript: str, classification: str, extraction_prompt: str, progress_callback=None) -> Dict:
        """Phase 2: Extract key elements based on classification"""
        try:
            if progress_callback:
                progress_callback("📊 Phase 2/3: Extracting key elements...")
            
            prompt = f"""Based on the classification: {classification}
            
{extraction_prompt}

Transcript:
{transcript[:10000]}"""  # Increased limit for extraction
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            extraction_result = message.content[0].text
            
            if progress_callback:
                progress_callback("✅ Extraction complete!")
            
            return {
                "success": True,
                "extracted_elements": extraction_result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_article(self, extracted_elements: str, writing_prompt: str, progress_callback=None) -> str:
        """Phase 3: Write the final article"""
        try:
            if progress_callback:
                progress_callback("✍️ Phase 3/3: Writing article...")
            
            prompt = f"""{writing_prompt}

Extracted Elements:
{extracted_elements}

Create a well-structured article based on these elements."""
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if progress_callback:
                progress_callback("✅ Article generation complete!")
            
            return message.content[0].text
        except Exception as e:
            return f"Error writing article: {str(e)}"
    
    def generate_article_3phase(self, transcript: str, prompts: Dict, progress_callback=None) -> Dict:
        """Complete 3-phase article generation"""
        results = {
            "classification": None,
            "extraction": None,
            "article": None,
            "success": True
        }
        
        # Phase 1: Classification
        classification_result = self.classify_content(
            transcript, 
            prompts["classification"], 
            progress_callback
        )
        
        if not classification_result["success"]:
            results["success"] = False
            results["error"] = classification_result["error"]
            return results
        
        results["classification"] = classification_result["classification"]
        
        # Phase 2: Extraction
        extraction_result = self.extract_elements(
            transcript,
            results["classification"],
            prompts["extraction"],
            progress_callback
        )
        
        if not extraction_result["success"]:
            results["success"] = False
            results["error"] = extraction_result["error"]
            return results
        
        results["extraction"] = extraction_result["extracted_elements"]
        
        # Phase 3: Writing
        article = self.write_article(
            results["extraction"],
            prompts["writing"],
            progress_callback
        )
        
        results["article"] = article
        
        return results


def apply_enhanced_css():
    st.markdown("""
    <style>
    /* Enhanced Color Scheme */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --accent-color: #ec4899;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Main Container Styling */
    .stApp {
        background: linear-gradient(180deg, #f8faff 0%, #f3f4f6 100%);
    }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        background: var(--bg-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05em;
    }
    
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.25rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    /* Card Styling */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }
    
    /* Phase Indicator */
    .phase-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 1rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .phase-item {
        flex: 1;
        text-align: center;
        padding: 1rem;
        position: relative;
    }
    
    .phase-item.active {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .phase-item.completed {
        color: var(--success-color);
    }
    
    .phase-number {
        display: inline-block;
        width: 35px;
        height: 35px;
        line-height: 35px;
        border-radius: 50%;
        background: #e5e7eb;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .phase-item.active .phase-number {
        background: var(--primary-color);
        color: white;
    }
    
    .phase-item.completed .phase-number {
        background: var(--success-color);
        color: white;
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--bg-gradient);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 12px;
        padding: 0.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-gradient);
        color: white;
    }
    
    /* Progress Messages */
    .progress-message {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border-left: 4px solid var(--primary-color);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #fafbff 0%, #f3f4f6 100%);
    }
    
    /* Success/Error Messages */
    .success-banner {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 1px solid #10b981;
        color: #065f46;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .error-banner {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 1px solid #ef4444;
        color: #991b1b;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    /* Prompt Editor */
    .prompt-editor {
        background: #f9fafb;
        border: 2px dashed #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .prompt-editor:hover {
        border-color: var(--primary-color);
        background: #f3f4f6;
    }
    </style>
    """, unsafe_allow_html=True)


def render_phase_indicator(current_phase: str = None):
    """Render the 3-phase progress indicator"""
    phases = [
        ("1", "Classification", "classification"),
        ("2", "Extraction", "extraction"),
        ("3", "Writing", "writing")
    ]
    
    html = '<div class="phase-indicator">'
    
    for num, name, key in phases:
        status = ""
        if current_phase == key:
            status = "active"
        elif current_phase and phases.index((num, name, key)) < [p[2] for p in phases].index(current_phase):
            status = "completed"
        
        html += f'''
        <div class="phase-item {status}">
            <div class="phase-number">{num}</div>
            <div>{name}</div>
        </div>
        '''
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="YouTube AI Article Generator - Pro",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_enhanced_css()
    
    # Initialize session state
    if 'transcript_data' not in st.session_state:
        st.session_state.transcript_data = None
    if 'structured_data' not in st.session_state:
        st.session_state.structured_data = None
    if 'video_id' not in st.session_state:
        st.session_state.video_id = None
    if 'plain_text' not in st.session_state:
        st.session_state.plain_text = None
    if 'generation_results' not in st.session_state:
        st.session_state.generation_results = None
    if 'article_generating' not in st.session_state:
        st.session_state.article_generating = False
    if 'custom_prompts' not in st.session_state:
        st.session_state.custom_prompts = DEFAULT_PROMPTS.copy()
    
    # Header
    st.markdown('<h1 class="main-header">🎬 YouTube AI Article Generator Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Advanced 3-Phase AI Article Generation with Custom Prompts</p>', unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        with st.expander("🔑 API Settings", expanded=True):
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Your Anthropic API key for Claude AI",
                placeholder="sk-ant-..."
            )
        
        st.divider()
        
        # Prompt Dashboard
        st.header("📝 Prompt Dashboard")
        st.caption("Customize prompts for each generation phase")
        
        with st.expander("🔍 Classification Prompt"):
            st.session_state.custom_prompts["classification"] = st.text_area(
                "Classification",
                value=st.session_state.custom_prompts["classification"],
                height=150,
                help="Prompt for content classification"
            )
        
        with st.expander("📊 Extraction Prompt"):
            st.session_state.custom_prompts["extraction"] = st.text_area(
                "Extraction",
                value=st.session_state.custom_prompts["extraction"],
                height=150,
                help="Prompt for element extraction"
            )
        
        with st.expander("✍️ Writing Prompt"):
            st.session_state.custom_prompts["writing"] = st.text_area(
                "Writing",
                value=st.session_state.custom_prompts["writing"],
                height=150,
                help="Prompt for article writing"
            )
        
        if st.button("🔄 Reset to Defaults", type="secondary"):
            st.session_state.custom_prompts = DEFAULT_PROMPTS.copy()
            st.rerun()
    
    # Main Content Area
    extractor = YouTubeTranscriptExtractor()
    
    # URL Input Section
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        
        with col1:
            youtube_url = st.text_input(
                "🎥 YouTube URL",
                placeholder="https://www.youtube.com/watch?v=example",
                help="Paste any YouTube video URL here",
                label_visibility="collapsed"
            )
        
        with col2:
            extract_button = st.button("🚀 Extract", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle transcript extraction
    if extract_button and youtube_url:
        video_id = extractor.extract_video_id(youtube_url)
        
        if not video_id:
            st.markdown('<div class="error-banner">❌ Invalid YouTube URL. Please check the format.</div>', unsafe_allow_html=True)
        else:
            with st.spinner("🔄 Extracting transcript..."):
                transcript_text, structured_data, plain_text = extractor.get_transcript_with_timestamps(video_id)
            
            if transcript_text.startswith("Error:"):
                st.markdown(f'<div class="error-banner">{transcript_text}</div>', unsafe_allow_html=True)
            else:
                st.session_state.transcript_data = transcript_text
                st.session_state.structured_data = structured_data
                st.session_state.video_id = video_id
                st.session_state.plain_text = plain_text
                st.session_state.generation_results = None
                
                st.markdown('<div class="success-banner">✅ Transcript extracted successfully!</div>', unsafe_allow_html=True)
    
    # Display content if transcript is available
    if st.session_state.transcript_data:
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Transcript", 
            "🤖 AI Generation", 
            "📊 Analysis",
            "💾 Downloads"
        ])
        
        with tab1:
            st.markdown("### 📝 Timestamped Transcript")
            st.text_area(
                "Transcript Content",
                value=st.session_state.transcript_data,
                height=600,
                label_visibility="collapsed"
            )
        
        with tab2:
            if not api_key:
                st.warning("🔑 Please enter your Anthropic API key in the sidebar to generate articles.")
            else:
                # Phase indicator
                render_phase_indicator()
                
                # Generation controls
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    if st.button("🎨 Generate Article", type="primary", disabled=st.session_state.article_generating):
                        st.session_state.article_generating = True
                        st.session_state.generation_results = None
                        st.rerun()
                
                with col2:
                    if st.session_state.generation_results:
                        if st.button("🔄 Regenerate", type="secondary"):
                            st.session_state.generation_results = None
                            st.rerun()
                
                # Progress container
                progress_container = st.empty()
                
                # Handle generation
                if st.session_state.article_generating and not st.session_state.generation_results:
                    def update_progress(message):
                        progress_container.markdown(f'<div class="progress-message">{message}</div>', unsafe_allow_html=True)
                    
                    try:
                        generator = EnhancedArticleGenerator(api_key)
                        
                        # Validate API key
                        is_valid, validation_message = generator.validate_api_key()
                        if not is_valid:
                            st.error(f"❌ {validation_message}")
                            st.session_state.article_generating = False
                            st.rerun()
                        
                        # Run 3-phase generation
                        results = generator.generate_article_3phase(
                            st.session_state.plain_text,
                            st.session_state.custom_prompts,
                            progress_callback=update_progress
                        )
                        
                        st.session_state.generation_results = results
                        st.session_state.article_generating = False
                        progress_container.empty()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.session_state.article_generating = False
                        st.rerun()
                
                # Display results
                if st.session_state.generation_results:
                    results = st.session_state.generation_results
                    
                    if results["success"]:
                        # Show phase results in expandable sections
                        with st.expander("🔍 Phase 1: Classification", expanded=False):
                            st.markdown("**Content Classification:**")
                            st.info(results["classification"])
                        
                        with st.expander("📊 Phase 2: Extraction", expanded=False):
                            st.markdown("**Extracted Elements:**")
                            st.info(results["extraction"])
                        
                        # Final article
                        st.markdown("### 📰 Generated Article")
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown(results["article"])
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Generation failed: {results.get('error', 'Unknown error')}")
        
        with tab3:
            st.markdown("### 📊 Transcript Analysis")
            
            if st.session_state.structured_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Segments", len(st.session_state.structured_data))
                
                with col2:
                    duration = extractor.format_timestamp(st.session_state.structured_data[-1]['start_seconds'])
                    st.metric("Video Duration", duration)
                
                with col3:
                    word_count = len(st.session_state.plain_text.split())
                    st.metric("Word Count", f"{word_count:,}")
                
                # Segment viewer
                st.markdown("#### 🔍 Transcript Segments")
                segments_to_show = st.slider("Number of segments to display", 5, 50, 10)
                
                for i, segment in enumerate(st.session_state.structured_data[:segments_to_show]):
                    with st.expander(f"[{segment['timestamp']}] Segment {i+1}"):
                        st.write(segment['text'])
        
        with tab4:
            st.markdown("### 💾 Download Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download Transcript (TXT)",
                    data=st.session_state.transcript_data,
                    file_name=f"transcript_{st.session_state.video_id}.txt",
                    mime="text/plain"
                )
                
                if st.session_state.generation_results and st.session_state.generation_results["success"]:
                    st.download_button(
                        label="📥 Download Article (MD)",
                        data=st.session_state.generation_results["article"],
                        file_name=f"article_{st.session_state.video_id}.md",
                        mime="text/markdown"
                    )
            
            with col2:
                json_data = json.dumps({
                    "video_id": st.session_state.video_id,
                    "segments": st.session_state.structured_data,
                    "generation_results": st.session_state.generation_results
                }, indent=2)
                
                st.download_button(
                    label="📥 Download Complete Data (JSON)",
                    data=json_data,
                    file_name=f"complete_data_{st.session_state.video_id}.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()