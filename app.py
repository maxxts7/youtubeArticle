import streamlit as st
import re
import json
from datetime import timedelta
from youtube_transcript_api import YouTubeTranscriptApi
import anthropic
from typing import List, Dict, Optional


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
    
    def get_transcript_with_timestamps(self, video_id: str) -> tuple[str, List[Dict]]:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            formatted_transcript = ""
            structured_transcript = []
            
            for entry in transcript_list:
                timestamp = self.format_timestamp(entry['start'])
                text = entry['text'].strip()
                
                formatted_transcript += f"[{timestamp}] {text}\n"
                structured_transcript.append({
                    'timestamp': timestamp,
                    'start_seconds': entry['start'],
                    'text': text
                })
            
            return formatted_transcript, structured_transcript
        except Exception as e:
            return f"Error: {str(e)}", []


class ArticleGenerator:
    def __init__(self, api_key: str):
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.api_key_valid = True
        except Exception as e:
            self.api_key_valid = False
            self.error_message = str(e)
    
    def validate_api_key(self) -> tuple[bool, str]:
        if not self.api_key_valid:
            return False, f"API key validation failed: {self.error_message}"
        return True, "API key is valid"
    
    def generate_article(self, transcript: str, custom_prompt: str, progress_callback=None) -> str:
        try:
            if progress_callback:
                progress_callback("🔑 Validating API key...")
            
            if not self.api_key_valid:
                return f"Error: API key validation failed - {self.error_message}"
            
            if progress_callback:
                progress_callback("📝 Preparing content for AI processing...")
            
            # Limit transcript length to avoid token limits
            max_transcript_length = 15000  # Roughly 3000-4000 tokens
            if len(transcript) > max_transcript_length:
                transcript = transcript[:max_transcript_length] + "\n\n[Note: Transcript truncated due to length]"
            
            base_prompt = f"""
You are a professional content writer. Based on the following YouTube video transcript, create a well-structured, engaging article.

Custom instructions: {custom_prompt}

Transcript:
{transcript}

Please create a comprehensive article that:
1. Has an engaging title and introduction
2. Is well-structured with clear sections and headers
3. Maintains the key information from the transcript
4. Is written in a professional, readable style
5. Includes relevant insights and analysis where appropriate

Format the output in clean markdown for easy reading.
"""
            
            if progress_callback:
                progress_callback("🤖 Sending request to Claude AI...")
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": base_prompt}]
            )
            
            if progress_callback:
                progress_callback("✅ Article generated successfully!")
            
            return message.content[0].text
        except Exception as e:
            error_msg = f"Error generating article: {str(e)}"
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return error_msg


def apply_custom_css():
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        text-align: center;
        color: #6c757d;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .transcript-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .article-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .success-message {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
    }
    
    .error-message {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
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
    
    apply_custom_css()
    
    # Initialize session state
    if 'transcript_data' not in st.session_state:
        st.session_state.transcript_data = None
    if 'structured_data' not in st.session_state:
        st.session_state.structured_data = None
    if 'video_id' not in st.session_state:
        st.session_state.video_id = None
    if 'generated_article' not in st.session_state:
        st.session_state.generated_article = None
    if 'article_generating' not in st.session_state:
        st.session_state.article_generating = False
    
    st.markdown('<h1 class="main-header">🎬 YouTube AI Article Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transform YouTube videos into professional articles with AI-powered insights</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("🔑 Configuration")
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Enter your Anthropic API key to enable article generation",
            placeholder="sk-ant-..."
        )
        
        st.header("📝 Article Customization")
        custom_prompt = st.text_area(
            "Custom Instructions",
            placeholder="e.g., 'Write in a technical style for developers' or 'Create a summary for business executives'",
            help="Provide specific instructions for how you want the article to be written",
            height=120
        )
        
        st.header("ℹ️ About")
        st.markdown("""
        **Features:**
        - ⏱️ Extract timestamped transcripts
        - 🤖 AI-powered article generation
        - 📄 Professional formatting
        - 💾 Download options
        - 🎨 Custom styling options
        """)
    
    extractor = YouTubeTranscriptExtractor()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        youtube_url = st.text_input(
            "🎥 YouTube URL",
            placeholder="https://www.youtube.com/watch?v=example",
            help="Paste any YouTube video URL here"
        )
    
    with col2:
        st.write("")
        st.write("")
        extract_button = st.button("🚀 Extract & Process", type="primary")
    
    if extract_button and youtube_url:
        video_id = extractor.extract_video_id(youtube_url)
        
        if not video_id:
            st.markdown('<div class="error-message">❌ Invalid YouTube URL. Please check the format.</div>', unsafe_allow_html=True)
            return
        
        with st.spinner("🔄 Extracting transcript with timestamps..."):
            transcript_text, structured_data = extractor.get_transcript_with_timestamps(video_id)
        
        if transcript_text.startswith("Error:"):
            st.markdown(f'<div class="error-message">{transcript_text}</div>', unsafe_allow_html=True)
        else:
            # Store in session state
            st.session_state.transcript_data = transcript_text
            st.session_state.structured_data = structured_data
            st.session_state.video_id = video_id
            st.session_state.generated_article = None  # Reset article when new transcript is loaded
            
            st.markdown('<div class="success-message">✅ Transcript extracted successfully!</div>', unsafe_allow_html=True)
    
    # Display tabs if we have transcript data
    if st.session_state.transcript_data:
        tab1, tab2, tab3 = st.tabs(["📄 Timestamped Transcript", "🤖 AI Article", "📊 Transcript Data"])
            
        with tab1:
            st.markdown('<div class="transcript-container">', unsafe_allow_html=True)
            st.markdown("### 📝 Transcript with Timestamps")
            st.text_area(
                "Full Transcript:",
                value=st.session_state.transcript_data,
                height=500,
                help="Transcript with timestamps - scroll to read the full content"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Transcript",
                    data=st.session_state.transcript_data,
                    file_name=f"youtube_transcript_{st.session_state.video_id}.txt",
                    mime="text/plain"
                )
            with col2:
                json_data = json.dumps(st.session_state.structured_data, indent=2)
                st.download_button(
                    label="📥 Download JSON Data",
                    data=json_data,
                    file_name=f"youtube_transcript_data_{st.session_state.video_id}.json",
                    mime="application/json"
                )
            
        with tab2:
            if not api_key:
                st.warning("🔑 Please enter your Anthropic API key in the sidebar to generate articles.")
            else:
                if not custom_prompt:
                    custom_prompt = "Create a comprehensive, well-structured article suitable for a general audience."
                
                # Progress tracking container
                progress_container = st.empty()
                status_container = st.empty()
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    generate_button = st.button("🎨 Generate Article", type="primary", disabled=st.session_state.article_generating)
                
                with col2:
                    if st.session_state.article_generating:
                        st.info("🔄 Article generation in progress...")
                
                # Handle article generation
                if generate_button and not st.session_state.article_generating:
                    st.session_state.article_generating = True
                    st.session_state.generated_article = None
                    st.rerun()
                
                # Progress tracking during generation
                if st.session_state.article_generating and not st.session_state.generated_article:
                    def update_progress(message):
                        progress_container.info(f"📊 Progress: {message}")
                    
                    try:
                        generator = ArticleGenerator(api_key)
                        
                        # Validate API key first
                        is_valid, validation_message = generator.validate_api_key()
                        if not is_valid:
                            status_container.error(f"❌ {validation_message}")
                            st.session_state.article_generating = False
                            st.rerun()
                        
                        update_progress("🚀 Starting article generation...")
                        
                        # Generate the article
                        article = generator.generate_article(
                            st.session_state.transcript_data, 
                            custom_prompt, 
                            progress_callback=update_progress
                        )
                        
                        # Store result and stop generating
                        st.session_state.generated_article = article
                        st.session_state.article_generating = False
                        progress_container.empty()
                        st.rerun()
                        
                    except Exception as e:
                        status_container.error(f"❌ Error: {str(e)}")
                        st.session_state.article_generating = False
                        st.rerun()
                
                # Display generated article
                if st.session_state.generated_article:
                    if st.session_state.generated_article.startswith("Error"):
                        st.error(st.session_state.generated_article)
                    else:
                        st.success("✅ Article generated successfully!")
                        st.markdown('<div class="article-container">', unsafe_allow_html=True)
                        st.markdown("### 📰 Generated Article")
                        st.markdown(st.session_state.generated_article)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.download_button(
                                label="📥 Download Article",
                                data=st.session_state.generated_article,
                                file_name=f"youtube_article_{st.session_state.video_id}.md",
                                mime="text/markdown"
                            )
                        with col2:
                            if st.button("🔄 Generate New Article"):
                                st.session_state.generated_article = None
                                st.rerun()
            
        with tab3:
            st.markdown("### 📊 Structured Transcript Data")
            if st.session_state.structured_data:
                st.write(f"**Total segments:** {len(st.session_state.structured_data)}")
                st.write(f"**Video duration:** ~{extractor.format_timestamp(st.session_state.structured_data[-1]['start_seconds'])}")
                
                st.markdown("#### 🔍 Transcript Segments")
                for i, segment in enumerate(st.session_state.structured_data[:10]):
                    with st.expander(f"[{segment['timestamp']}] Segment {i+1}"):
                        st.write(segment['text'])
                
                if len(st.session_state.structured_data) > 10:
                    st.info(f"Showing first 10 segments. Total: {len(st.session_state.structured_data)} segments")


if __name__ == "__main__":
    main()