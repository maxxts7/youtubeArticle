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
    
    "extraction": """Extract the following elements from this transcript and present them in clear, natural language:

**Key Ideas**: What are the main concepts and themes discussed? Explain each one clearly.

**Topic Introductions**: How are new topics introduced throughout the content? What transition methods are used?

**Supporting Evidence**: What data, facts, statistics, or evidence is provided to support claims? List specific examples.

**Analogies and Comparisons**: What comparisons, metaphors, or analogies are used to explain concepts? Describe them in detail.

**Unique Insights**: What unique perspectives, realizations, or "aha moments" are shared? Explain their significance.

**Concrete Examples**: What specific examples, case studies, or stories are mentioned? Describe them clearly.

**Additional Elements**: Any other notable patterns, techniques, or elements worth highlighting.

Write each section in clear, natural language that someone unfamiliar with the content can easily understand.""",
    
    "writing": """Based on the extracted elements, write an article following these principles:
- Minimize words, maximize clarity
- Imply don't explain
- Facts over commentary
- Clear structure with headings
- Engaging but concise"""
}

# Default model settings
DEFAULT_MODEL_SETTINGS = {
    "classification_model": "claude-3-5-sonnet-20241022",
    "extraction_model": "claude-3-5-sonnet-20241022", 
    "writing_model": "claude-3-5-sonnet-20241022",
    "classification_max_tokens": 500,
    "extraction_max_tokens": 3000,
    "writing_max_tokens": 4000,
    "classification_temperature": 0.3,
    "extraction_temperature": 0.5,
    "writing_temperature": 0.7
}

# Available Claude models
AVAILABLE_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022", 
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-4-opus-20250514",
    "claude-4-sonnet-20250514"
]


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
    def __init__(self, api_key: str, model_settings: Dict):
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.api_key_valid = True
            self.model_settings = model_settings
        except Exception as e:
            self.api_key_valid = False
            self.error_message = str(e)
    
    def validate_api_key(self) -> Tuple[bool, str]:
        if not self.api_key_valid:
            return False, f"API key validation failed: {self.error_message}"
        return True, "API key is valid"
    
    def classify_content(self, transcript: str, classification_prompt: str) -> Dict:
        """Phase 1: Classify the content type"""
        try:
            prompt = f"{classification_prompt}\n\nTranscript:\n{transcript[:5000]}"  # Limit for classification
            
            message = self.client.messages.create(
                model=self.model_settings["classification_model"],
                max_tokens=self.model_settings["classification_max_tokens"],
                temperature=self.model_settings["classification_temperature"],
                messages=[{"role": "user", "content": prompt}]
            )
            
            classification_result = message.content[0].text
            
            return {
                "success": True,
                "classification": classification_result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_elements(self, transcript: str, classification: str, extraction_prompt: str) -> Dict:
        """Phase 2: Extract key elements based on classification"""
        try:
            prompt = f"""Based on the classification: {classification}
            
{extraction_prompt}

Transcript:
{transcript[:15000]}"""  # Increased limit for extraction
            
            message = self.client.messages.create(
                model=self.model_settings["extraction_model"],
                max_tokens=self.model_settings["extraction_max_tokens"],
                temperature=self.model_settings["extraction_temperature"],
                messages=[{"role": "user", "content": prompt}]
            )
            
            extraction_result = message.content[0].text
            
            return {
                "success": True,
                "extracted_elements": extraction_result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_article(self, extracted_elements: str, writing_prompt: str) -> str:
        """Phase 3: Write the final article"""
        try:
            prompt = f"""{writing_prompt}

Extracted Elements:
{extracted_elements}

Create a well-structured article based on these elements."""
            
            message = self.client.messages.create(
                model=self.model_settings["writing_model"],
                max_tokens=self.model_settings["writing_max_tokens"],
                temperature=self.model_settings["writing_temperature"],
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
        except Exception as e:
            return f"Error writing article: {str(e)}"


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
    
    /* Phase Card */
    .phase-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin: 2rem 0;
        border-left: 4px solid var(--primary-color);
    }
    
    .phase-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .phase-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .phase-status.active {
        background: var(--primary-color);
        color: white;
    }
    
    .phase-status.completed {
        background: var(--success-color);
        color: white;
    }
    
    .phase-status.pending {
        background: #e5e7eb;
        color: #6b7280;
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
    
    /* API Key Card */
    .api-key-card {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border: 2px solid var(--primary-color);
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem auto;
        max-width: 600px;
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
    
    /* Result Box */
    .result-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Prompt Editor */
    .prompt-editor {
        background: #f9fafb;
        border: 2px dashed #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .prompt-editor:hover {
        border-color: var(--primary-color);
        background: #f3f4f6;
    }
    
    /* Success/Error Messages */
    .success-message {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 1px solid #10b981;
        color: #065f46;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .error-message {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 1px solid #ef4444;
        color: #991b1b;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
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
    </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="YouTube AI Article Generator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_enhanced_css()
    
    # Initialize session state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    if 'api_key_validated' not in st.session_state:
        st.session_state.api_key_validated = False
    if 'transcript_data' not in st.session_state:
        st.session_state.transcript_data = None
    if 'structured_data' not in st.session_state:
        st.session_state.structured_data = None
    if 'video_id' not in st.session_state:
        st.session_state.video_id = None
    if 'plain_text' not in st.session_state:
        st.session_state.plain_text = None
    if 'current_phase' not in st.session_state:
        st.session_state.current_phase = None
    if 'classification_result' not in st.session_state:
        st.session_state.classification_result = None
    if 'extraction_result' not in st.session_state:
        st.session_state.extraction_result = None
    if 'article_result' not in st.session_state:
        st.session_state.article_result = None
    if 'custom_prompts' not in st.session_state:
        st.session_state.custom_prompts = DEFAULT_PROMPTS.copy()
    if 'model_settings' not in st.session_state:
        st.session_state.model_settings = DEFAULT_MODEL_SETTINGS.copy()
    
    # Header
    st.markdown('<h1 class="main-header">🎬 YouTube AI Article Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transform YouTube videos into professional articles with AI</p>', unsafe_allow_html=True)
    
    # API Key Setup (First Time)
    if not st.session_state.api_key_validated:
        st.markdown('<div class="api-key-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Welcome! Let's get started")
        st.markdown("Please enter your Anthropic API key to begin generating articles.")
        
        api_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Your API key will be used only for this session"
        )
        
        if st.button("🚀 Start Using App", type="primary", disabled=not api_key_input):
            # Validate API key
            generator = EnhancedArticleGenerator(api_key_input, DEFAULT_MODEL_SETTINGS)
            is_valid, message = generator.validate_api_key()
            
            if is_valid:
                st.session_state.api_key = api_key_input
                st.session_state.api_key_validated = True
                st.rerun()
            else:
                st.error(f"❌ {message}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Sidebar - Configuration Dashboard
    with st.sidebar:
        st.header("⚙️ Configuration Dashboard")
        
        # Show transcript if available
        if st.session_state.transcript_data:
            with st.expander("📄 View Transcript", expanded=False):
                st.text_area(
                    "Transcript",
                    value=st.session_state.transcript_data,
                    height=300,
                    label_visibility="collapsed"
                )
        
        st.divider()
        
        # Model Settings
        st.subheader("🤖 Model Settings")
        
        with st.expander("⚙️ Model Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Classification**")
                st.session_state.model_settings["classification_model"] = st.selectbox(
                    "Model",
                    AVAILABLE_MODELS,
                    index=AVAILABLE_MODELS.index(st.session_state.model_settings["classification_model"]),
                    key="class_model"
                )
                st.session_state.model_settings["classification_max_tokens"] = st.number_input(
                    "Max Tokens",
                    min_value=100,
                    max_value=8192,
                    value=st.session_state.model_settings["classification_max_tokens"],
                    key="class_tokens"
                )
                st.session_state.model_settings["classification_temperature"] = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.model_settings["classification_temperature"],
                    step=0.1,
                    key="class_temp"
                )
            
            with col2:
                st.markdown("**Extraction**")
                st.session_state.model_settings["extraction_model"] = st.selectbox(
                    "Model",
                    AVAILABLE_MODELS,
                    index=AVAILABLE_MODELS.index(st.session_state.model_settings["extraction_model"]),
                    key="extract_model"
                )
                st.session_state.model_settings["extraction_max_tokens"] = st.number_input(
                    "Max Tokens",
                    min_value=100,
                    max_value=8192,
                    value=st.session_state.model_settings["extraction_max_tokens"],
                    key="extract_tokens"
                )
                st.session_state.model_settings["extraction_temperature"] = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.model_settings["extraction_temperature"],
                    step=0.1,
                    key="extract_temp"
                )
            
            st.markdown("**Writing**")
            col3, col4, col5 = st.columns(3)
            with col3:
                st.session_state.model_settings["writing_model"] = st.selectbox(
                    "Model",
                    AVAILABLE_MODELS,
                    index=AVAILABLE_MODELS.index(st.session_state.model_settings["writing_model"]),
                    key="write_model"
                )
            with col4:
                st.session_state.model_settings["writing_max_tokens"] = st.number_input(
                    "Max Tokens",
                    min_value=100,
                    max_value=8192,
                    value=st.session_state.model_settings["writing_max_tokens"],
                    key="write_tokens"
                )
            with col5:
                st.session_state.model_settings["writing_temperature"] = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.model_settings["writing_temperature"],
                    step=0.1,
                    key="write_temp"
                )
        
        st.divider()
        
        # Prompt customization
        st.subheader("📝 Customize Prompts")
        
        with st.expander("🔍 Classification Prompt"):
            st.session_state.custom_prompts["classification"] = st.text_area(
                "Classification",
                value=st.session_state.custom_prompts["classification"],
                height=200,
                label_visibility="collapsed"
            )
        
        with st.expander("📊 Extraction Prompt"):
            st.session_state.custom_prompts["extraction"] = st.text_area(
                "Extraction",
                value=st.session_state.custom_prompts["extraction"],
                height=300,
                label_visibility="collapsed"
            )
        
        with st.expander("✍️ Writing Prompt"):
            st.session_state.custom_prompts["writing"] = st.text_area(
                "Writing",
                value=st.session_state.custom_prompts["writing"],
                height=200,
                label_visibility="collapsed"
            )
        
        if st.button("🔄 Reset All to Defaults"):
            st.session_state.custom_prompts = DEFAULT_PROMPTS.copy()
            st.session_state.model_settings = DEFAULT_MODEL_SETTINGS.copy()
            st.rerun()
    
    # Main Content Area
    extractor = YouTubeTranscriptExtractor()
    generator = EnhancedArticleGenerator(st.session_state.api_key, st.session_state.model_settings)
    
    # Step 1: YouTube URL Input
    if not st.session_state.transcript_data:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🎥 Step 1: Enter YouTube URL")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                youtube_url = st.text_input(
                    "YouTube URL",
                    placeholder="https://www.youtube.com/watch?v=example",
                    label_visibility="collapsed"
                )
            
            with col2:
                if st.button("🚀 Extract", type="primary", use_container_width=True):
                    if youtube_url:
                        video_id = extractor.extract_video_id(youtube_url)
                        
                        if not video_id:
                            st.error("❌ Invalid YouTube URL. Please check the format.")
                        else:
                            with st.spinner("🔄 Extracting transcript..."):
                                transcript_text, structured_data, plain_text = extractor.get_transcript_with_timestamps(video_id)
                            
                            if transcript_text.startswith("Error:"):
                                st.error(transcript_text)
                            else:
                                st.session_state.transcript_data = transcript_text
                                st.session_state.structured_data = structured_data
                                st.session_state.video_id = video_id
                                st.session_state.plain_text = plain_text
                                st.session_state.current_phase = "ready"
                                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Step 2: Article Generation Workflow
    elif st.session_state.transcript_data:
        # Show current status
        if st.session_state.current_phase == "ready":
            st.success("✅ Transcript extracted successfully!")
            
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### 🤖 Ready to Generate Article")
                st.markdown("Click the button below to start the AI-powered article generation process.")
                
                if st.button("🎨 Generate Article", type="primary"):
                    st.session_state.current_phase = "classification"
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Phase 1: Classification
        elif st.session_state.current_phase == "classification":
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.markdown('<div class="phase-header">🔍 Phase 1: Content Classification <span class="phase-status active">Active</span></div>', unsafe_allow_html=True)
            
            if not st.session_state.classification_result:
                with st.spinner("Analyzing content type..."):
                    result = generator.classify_content(
                        st.session_state.plain_text,
                        st.session_state.custom_prompts["classification"]
                    )
                    
                    if result["success"]:
                        st.session_state.classification_result = result["classification"]
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result['error']}")
            else:
                st.markdown("**Classification Result:**")
                st.info(st.session_state.classification_result)
                
                st.markdown("**Prompt Used:**")
                with st.expander("View/Edit Classification Prompt"):
                    new_prompt = st.text_area(
                        "Classification Prompt",
                        value=st.session_state.custom_prompts["classification"],
                        height=150,
                        label_visibility="collapsed"
                    )
                    if new_prompt != st.session_state.custom_prompts["classification"]:
                        st.session_state.custom_prompts["classification"] = new_prompt
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Continue to Extraction", type="primary"):
                        st.session_state.current_phase = "extraction"
                        st.rerun()
                with col2:
                    if st.button("🔄 Re-classify"):
                        st.session_state.classification_result = None
                        st.rerun()
                with col3:
                    if st.button("❌ Start Over"):
                        st.session_state.transcript_data = None
                        st.session_state.classification_result = None
                        st.session_state.current_phase = None
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Phase 2: Extraction
        elif st.session_state.current_phase == "extraction":
            # Show classification as completed
            with st.expander("✅ Phase 1: Classification (Completed)", expanded=False):
                st.info(st.session_state.classification_result)
            
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.markdown('<div class="phase-header">📊 Phase 2: Element Extraction <span class="phase-status active">Active</span></div>', unsafe_allow_html=True)
            
            if not st.session_state.extraction_result:
                with st.spinner("Extracting key elements..."):
                    result = generator.extract_elements(
                        st.session_state.plain_text,
                        st.session_state.classification_result,
                        st.session_state.custom_prompts["extraction"]
                    )
                    
                    if result["success"]:
                        st.session_state.extraction_result = result["extracted_elements"]
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result['error']}")
            else:
                st.markdown("**Extracted Elements:**")
                st.info(st.session_state.extraction_result)
                
                st.markdown("**Prompt Used:**")
                with st.expander("View/Edit Extraction Prompt"):
                    new_prompt = st.text_area(
                        "Extraction Prompt",
                        value=st.session_state.custom_prompts["extraction"],
                        height=150,
                        label_visibility="collapsed"
                    )
                    if new_prompt != st.session_state.custom_prompts["extraction"]:
                        st.session_state.custom_prompts["extraction"] = new_prompt
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Continue to Writing", type="primary"):
                        st.session_state.current_phase = "writing"
                        st.rerun()
                with col2:
                    if st.button("🔄 Re-extract"):
                        st.session_state.extraction_result = None
                        st.rerun()
                with col3:
                    if st.button("⬅️ Back to Classification"):
                        st.session_state.current_phase = "classification"
                        st.session_state.extraction_result = None
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Phase 3: Writing
        elif st.session_state.current_phase == "writing":
            # Show previous phases as completed
            with st.expander("✅ Phase 1: Classification (Completed)", expanded=False):
                st.info(st.session_state.classification_result)
            
            with st.expander("✅ Phase 2: Extraction (Completed)", expanded=False):
                st.info(st.session_state.extraction_result)
            
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.markdown('<div class="phase-header">✍️ Phase 3: Article Writing <span class="phase-status active">Active</span></div>', unsafe_allow_html=True)
            
            # Show writing prompt editor first
            st.markdown("**Customize Writing Prompt:**")
            with st.expander("Edit Writing Prompt", expanded=True):
                new_prompt = st.text_area(
                    "Writing Prompt",
                    value=st.session_state.custom_prompts["writing"],
                    height=150,
                    label_visibility="collapsed"
                )
                if new_prompt != st.session_state.custom_prompts["writing"]:
                    st.session_state.custom_prompts["writing"] = new_prompt
            
            # Generate button
            if st.button("✍️ Generate Article", type="primary"):
                with st.spinner("Writing article..."):
                    article = generator.write_article(
                        st.session_state.extraction_result,
                        st.session_state.custom_prompts["writing"]
                    )
                    st.session_state.article_result = article
                    st.session_state.current_phase = "completed"
                    st.rerun()
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Extraction"):
                    st.session_state.current_phase = "extraction"
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Completed State
        elif st.session_state.current_phase == "completed":
            # Show all phases as completed
            with st.expander("✅ Phase 1: Classification (Completed)", expanded=False):
                st.info(st.session_state.classification_result)
            
            with st.expander("✅ Phase 2: Extraction (Completed)", expanded=False):
                st.info(st.session_state.extraction_result)
            
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.markdown('<div class="phase-header">📰 Generated Article <span class="phase-status completed">Completed</span></div>', unsafe_allow_html=True)
            
            # Display the article
            st.markdown("### Your Article")
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.article_result)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.download_button(
                    label="📥 Download Article",
                    data=st.session_state.article_result,
                    file_name=f"article_{st.session_state.video_id}.md",
                    mime="text/markdown"
                )
            
            with col2:
                if st.button("🔄 Regenerate Article"):
                    st.session_state.article_result = None
                    st.session_state.current_phase = "writing"
                    st.rerun()
            
            with col3:
                if st.button("📝 New Article"):
                    # Reset everything except API key
                    st.session_state.transcript_data = None
                    st.session_state.structured_data = None
                    st.session_state.video_id = None
                    st.session_state.plain_text = None
                    st.session_state.current_phase = None
                    st.session_state.classification_result = None
                    st.session_state.extraction_result = None
                    st.session_state.article_result = None
                    st.rerun()
            
            with col4:
                # Export all data
                all_data = {
                    "video_id": st.session_state.video_id,
                    "classification": st.session_state.classification_result,
                    "extraction": st.session_state.extraction_result,
                    "article": st.session_state.article_result,
                    "prompts_used": st.session_state.custom_prompts
                }
                st.download_button(
                    label="📊 Export All Data",
                    data=json.dumps(all_data, indent=2),
                    file_name=f"complete_{st.session_state.video_id}.json",
                    mime="application/json"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()