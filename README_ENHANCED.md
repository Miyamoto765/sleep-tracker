# AI Sleep Tracker - Enhanced Real-Time Voice Analysis

A modern, professional sleep pattern tracking platform featuring real-time voice analysis, advanced analytics, and responsive web design.

## 🆕 New Features

### Real-Time Voice Recording
- **Browser Microphone Integration**: Direct audio capture using Web Audio API
- **Live Waveform Visualization**: Real-time audio feedback during recording
- **Tabbed Interface**: Seamless switching between live recording and file upload
- **Recording Controls**: Start, stop, pause, resume functionality
- **Download Options**: Save recorded audio locally

### Advanced Analytics Dashboard
- **Multi-Source Data Integration**: Combines uploads, real-time recordings, and database data
- **Comprehensive Chart Types**:
  - Sleep stage distribution with interactive pie charts
  - Confidence score trends over time
  - Hourly and daily pattern analysis
  - Sleep stage transition heatmaps
  - Monthly summary reports
- **Filtering System**: Filter by date range, sleep stages, and data sources
- **Export Functionality**: Download data as CSV or JSON

### Professional Website Features
- **Responsive Design**: Mobile-optimized interface with touch-friendly controls
- **Enhanced Error Handling**: User-friendly error messages with suggested actions
- **Loading Animations**: Smooth progress indicators
- **Modern UI**: Glassmorphism effects with gradient backgrounds
- **Performance Optimization**: Efficient audio processing and caching

### Technical Improvements
- **Audio Processing Pipeline**: Real-time feature extraction with buffering
- **Session Management**: Persistent recording sessions with SQLite backend
- **Error Handling Framework**: Comprehensive error recovery and logging
- **Database Integration**: Structured data storage with export capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Modern web browser with microphone permissions
- Audio recording device (microphone)

### Installation

1. **Clone and navigate to project**:
   ```bash
   cd sleep-tracker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app/streamlit_app.py
   ```

4. **Open in browser**:
   Navigate to `http://localhost:8501`

## 📖 Usage Guide

### Real-Time Recording
1. Navigate to the **"Real-time"** tab
2. Click **"Start Recording"** to begin audio capture
3. Speak clearly into your microphone (15-60 seconds recommended)
4. Click **"Stop Recording"** when finished
5. View instant sleep pattern analysis with confidence scores
6. Download recording if desired

### File Upload (Traditional)
1. Navigate to the **"Upload"** tab
2. Drag and drop or select audio file (WAV, MP3, FLAC, OGG)
3. View analysis results and MFCC visualizations
4. Access upload history in sidebar

### Analytics Dashboard
1. Navigate to the **"Analytics"** tab
2. Use filters to focus on specific time periods or sleep stages
3. Explore different chart types in the tabbed interface:
   - **Overview**: Key metrics and distribution charts
   - **Trends**: Time-based analysis and patterns
   - **Patterns**: Correlation and transition analysis
   - **Calendar**: Heatmap views and monthly summaries
4. Export data for external analysis

## 🏗️ Architecture

### Frontend Components
- **`app/streamlit_app.py`**: Main application with navigation
- **`app/views/`**: Feature-specific page components
- **`app/ui.py`**: Styling and responsive design

### Backend Services
- **`src/audio_processor.py`**: Real-time audio processing pipeline
- **`src/session_manager.py`**: Database operations and session management
- **`src/error_handlers.py`**: Error handling and user feedback
- **`src/feature_extraction.py`**: Audio feature extraction for ML

### Data Storage
- **SQLite Database**: Structured storage for recordings and predictions
- **File System**: Audio file storage with organized directory structure
- **CSV Exports**: Legacy support for existing data formats

## 🔧 Configuration

### Audio Settings
- **Sample Rate**: 22050 Hz (configurable)
- **Chunk Duration**: 5 seconds (configurable)
- **Supported Formats**: WAV, MP3, FLAC, OGG
- **Max File Size**: 50MB (configurable)

### Performance Settings
- **Database Path**: `data/sleep_tracker.db`
- **Recording Directory**: `data/recordings/`
- **Upload Directory**: `data/uploads/`
- **Cache Directory**: Streamlit default cache

## 🎯 Key Features

### Sleep Stage Classification
- **Wake**: Active/awake state detection
- **Light Sleep**: Initial sleep phase analysis
- **Deep Sleep**: Restorative sleep identification
- **REM**: Dream state pattern recognition

### Confidence Scoring
- **Model Confidence**: 0-100% prediction reliability
- **Feature Quality**: Audio analysis quality metrics
- **Real-time Feedback**: Instant confidence visualization

### Data Export Options
- **CSV Format**: Spreadsheet-compatible data export
- **JSON Format**: Structured data for API integration
- **Session Reports**: Complete analysis summaries

## 📱 Mobile Compatibility

### Touch-Optimized Interface
- **44px Minimum Touch Targets**:符合移动端可访问性标准
- **Responsive Navigation**: Collapsible menus for small screens
- **Adaptive Charts**: Automatically resized visualizations

### Performance Features
- **Progressive Loading**: Faster initial page loads
- **Background Processing**: Non-blocking audio analysis
- **Error Recovery**: Graceful handling of network issues

## 🔒 Privacy & Security

### Data Handling
- **Local Storage**: All processing happens locally in browser
- **No Cloud Uploads**: Audio data never leaves your device
- **Session Isolation**: User data kept separate and secure

### Permissions
- **Microphone Access**: Only when explicitly requested by user
- **File Access**: Limited to user-selected files
- **Browser Storage**: Minimal and transparent usage

## 🐛 Troubleshooting

### Common Issues

**Microphone Not Working**
- Check browser permissions for microphone access
- Ensure microphone is not muted in system settings
- Try refreshing the page and re-granting permissions

**Audio Quality Issues**
- Use a quiet environment for best results
- Keep device 6-12 inches from mouth
- Avoid background noise and interference

**Analysis Taking Too Long**
- Check internet connection stability
- Try shorter audio recordings (15-30 seconds)
- Clear browser cache if issues persist

**Charts Not Loading**
- Ensure browser supports modern JavaScript
- Check for browser extension conflicts
- Try using a different browser (Chrome/Firefox recommended)

### Error Messages
- **"Microphone access denied"**: Grant microphone permissions in browser settings
- **"Audio processing failed"**: Check file format and size limits
- **"Model unavailable"**: Refresh page and try again

## 📊 Performance Metrics

### Expected Performance
- **Recording Latency**: < 2 seconds from start to analysis
- **Chart Load Time**: < 3 seconds for complex visualizations
- **Mobile Compatibility**: > 95% feature availability on mobile devices
- **Error Rate**: < 5% for recording and processing operations

### Optimization Features
- **Lazy Loading**: Components load as needed
- **Audio Compression**: Efficient data transmission
- **Database Indexing**: Fast query performance
- **Cache Management**: Optimized repeated operations

## 🤝 Contributing

### Development Setup
1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-mock
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. Start development server:
   ```bash
   streamlit run app/streamlit_app.py --server.port 8501
   ```

### Code Style
- **Python**: Follow PEP 8 style guide
- **JavaScript**: ES6+ standards
- **CSS**: Mobile-first responsive design
- **Documentation**: Clear comments and docstrings

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔮 Future Roadmap

### Planned Enhancements
- **Multi-language Support**: International interface options
- **Sleep Recommendations**: Personalized sleep tips based on patterns
- **Integration APIs**: Connect with health tracking platforms
- **Advanced ML Models**: Deep learning for improved accuracy
- **Collaborative Features**: Shared sleep data for research (opt-in)

### Technology Improvements
- **WebRTC**: Real-time communication capabilities
- **PWA Support**: Offline functionality and app installation
- **Cloud Sync**: Optional data backup and synchronization
- **Voice Commands**: Hands-free operation

---

**Built with ❤️ using Streamlit, Librosa, and modern web technologies**