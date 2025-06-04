# 🎬 YouTube AI Article Generator

A professional Streamlit web application that extracts timestamped transcripts from YouTube videos and transforms them into high-quality articles using Anthropic's Claude AI.

## ✨ Features

### Core Functionality
- **📝 Timestamped Transcript Extraction**: Get precise timestamps with each segment
- **🤖 AI-Powered Article Generation**: Transform transcripts into professional articles
- **🎨 Custom Article Prompts**: Tailor articles for specific audiences or styles
- **📊 Structured Data Export**: Download transcript data in JSON format

### User Experience
- **🎨 High-End Visual Design**: Modern gradient UI with smooth animations
- **📱 Responsive Layout**: Works on desktop and mobile devices
- **🔄 Real-time Processing**: Live feedback during extraction and generation
- **💾 Multiple Download Options**: Text, Markdown, and JSON formats

### Technical Features
- **⚡ Fast Processing**: Efficient transcript extraction and AI generation
- **🔒 Secure API Integration**: Safe handling of Anthropic API keys
- **📈 Scalable Architecture**: Modular design for easy feature expansion
- **🛡️ Error Handling**: Comprehensive error messages and validation

## 🚀 Installation

1. **Clone or download the project**
2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Get your Anthropic API key** from [Anthropic Console](https://console.anthropic.com/)

## 💻 Usage

1. **Start the application:**
```bash
streamlit run app.py
```

2. **Open your browser** to the displayed URL (typically http://localhost:8501)

3. **Configure the app:**
   - Enter your Anthropic API key in the sidebar
   - Add custom instructions for article generation (optional)

4. **Process a video:**
   - Paste a YouTube URL
   - Click "🚀 Extract & Process"
   - View results in the organized tabs

## 📋 Features Overview

### 📄 Timestamped Transcript Tab
- View full transcript with precise timestamps
- Download as formatted text file
- Export structured data as JSON

### 🤖 AI Article Tab
- Generate professional articles from transcripts
- Customize writing style with custom prompts
- Download articles in Markdown format

### 📊 Transcript Data Tab
- View transcript statistics and segments
- Browse individual transcript segments
- Analyze video duration and structure

## 🎯 Use Cases

- **📚 Content Creation**: Transform video content into blog posts
- **📝 Research**: Convert educational videos into study materials
- **💼 Business**: Create meeting summaries from recorded sessions
- **🎓 Education**: Generate lecture notes from educational content
- **📖 Documentation**: Convert tutorial videos into written guides

## 🔧 Technical Architecture

- **Frontend**: Streamlit with custom CSS styling
- **Transcript Extraction**: youtube-transcript-api
- **AI Processing**: Anthropic Claude API
- **Data Handling**: JSON structure for transcript segments
- **UI Components**: Gradient designs, responsive layouts, tab organization

## 🔮 Future Enhancements

- **🌍 Multiple Language Support**: Extract transcripts in different languages
- **📊 Advanced Analytics**: Video content analysis and insights
- **🔍 Search Functionality**: Find specific content within transcripts
- **📤 Export Options**: PDF, DOCX, and other format support
- **🤝 Team Features**: Collaboration and sharing capabilities
- **📱 Mobile App**: Native mobile application
- **🔗 Integration APIs**: Connect with other content management systems