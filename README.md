# 🎭 SadTalker AI - Talking Head Generator

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

A powerful AI-powered web application that generates realistic talking head videos from a single portrait image and audio input. Built on top of the SadTalker model with a modern, user-friendly web interface.

![SadTalker AI Banner](docs/sadtalker_logo.png)

## ✨ Features

- 🎨 **Modern Web UI** - Beautiful, responsive interface with real-time progress tracking
- 🎥 **Video Generation** - Create realistic talking head videos from images and audio
- 🎭 **Face Enhancement** - Optional GFPGAN integration for enhanced face quality
- 🎬 **Reference Video Support** - Use reference videos for pose and expression guidance
- ⚡ **Real-time Progress** - Live progress updates during video generation
- 🖼️ **Batch Processing** - Support for processing multiple files
- 🔧 **Customizable Settings** - Fine-tune generation parameters for optimal results

## 🚀 Quick Start

### Prerequisites

- Python 3.10
- Windows/Linux/macOS
- CUDA-capable GPU (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Prathameshpatil4172/SadTalker-ai.git
   cd SadTalker-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv310
   venv310\Scripts\activate  # Windows
   source venv310/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download checkpoints** (required models)
   - Download checkpoint files and place them in the `checkpoints/` directory
   - Download GFPGAN models for face enhancement (optional)

5. **Run the application**
   ```bash
   # Using the launcher
   python launcher.py
   
   # Or run Flask app directly
   python app_flask.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 📖 Usage Guide

### Web Interface

1. **Upload Source Image** - Select a portrait image (front-facing works best)
2. **Upload Audio** - Choose an audio file (WAV format recommended)
3. **Configure Settings** (Optional):
   - **Preprocessing**: Crop, resize, or full image mode
   - **Still Mode**: Generate with minimal head movement
   - **Face Enhancer**: Enable GFPGAN for better face quality
   - **Reference Video**: Use a video for pose guidance
4. **Generate** - Click the generate button and watch the progress
5. **Download** - Save your generated video

### API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate video (multipart/form-data)
- `GET /status/<filename>` - Check generation progress
- `GET /video/<filename>` - Download generated video

## 🏗️ Project Structure

```
SadTalker-ai/
├── app/                    # React frontend application
├── src/                    # Core SadTalker source code
│   ├── facerender/        # Face rendering modules
│   ├── face3d/            # 3D face processing
│   └── utils/             # Utility functions
├── static/                # Static web assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── results/          # Generated videos
├── uploads/               # User uploaded files
├── checkpoints/           # Model checkpoints
├── gfpgan/               # Face enhancement models
├── app_flask.py          # Flask backend application
├── launcher.py           # Setup and launch script
├── unified.html          # Main web interface
└── requirements.txt      # Python dependencies
```

## 🎨 Screenshots

### Main Interface
![Main Interface](docs/screenshots/main_interface.png)
*The main web interface with upload controls and settings*

> **Note:** To add screenshots, save your images to `docs/screenshots/` directory with the following filenames:
> - `main_interface.png` - Main web interface
> - `progress.png` - Generation progress screen
> - `results.png` - Results gallery
> - `settings.png` - Settings panel

### Example Results

**Original SadTalker Examples:**

| Crop Mode | Full Mode | Enhanced |
|-----------|-----------|----------|
| ![Crop](docs/example_crop.gif) | ![Full](docs/example_full.gif) | ![Enhanced](docs/example_full_enhanced.gif) |

**Reference Video Mode:**
![Reference Video](docs/using_ref_video.gif)

**3D Face View:**
![3D View](docs/free_view_result.gif)

## ⚙️ Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| Preprocess | Image preprocessing mode | `crop` |
| Still Mode | Minimal head movement | `false` |
| Face Enhancer | Enable GFPGAN | `false` |
| Batch Size | Processing batch size | `2` |
| Expression Scale | Facial expression intensity | `1.0` |
| Pose Style | Head pose style | `0` |

## 🔧 Advanced Features

### Reference Video Mode
Use a reference video to guide the head pose and expressions:
1. Enable "Use Reference Video"
2. Upload a reference video
3. Select reference mode (pose/full)

### Idle Mode
Generate videos with natural idle animations:
1. Enable "Idle Mode"
2. Set desired video length
3. Configure blink settings

## 📝 Requirements

### System Requirements
- **OS**: Windows 10/11, Linux, macOS
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA GPU with 4GB+ VRAM (CUDA 11.7+)
- **Storage**: 10GB free space

### Python Packages
Key dependencies (see `requirements.txt` for complete list):
- Flask >= 2.0.0
- torch >= 1.12.0
- torchvision >= 0.13.0
- opencv-python >= 4.6.0
- numpy >= 1.21.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original [SadTalker](https://github.com/OpenTalker/SadTalker) by OpenTalker
- [GFPGAN](https://github.com/TencentARC/GFPGAN) for face enhancement
- [Flask](https://flask.palletsprojects.com/) web framework

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ by [Prathamesh Patil](https://github.com/Prathameshpatil4172)
