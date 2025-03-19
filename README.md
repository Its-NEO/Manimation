# Genimation: Mathematical Visualization Tool

Genimation is a web application that uses AI to create beautiful mathematical visualizations with Manim, a mathematical animation engine.

## Features

- 🧮 Generate visualizations of mathematical concepts and expressions using AI
- 🎬 Automatically render and stream high-quality mathematical animations
- 💬 Chat with an AI assistant about mathematical concepts and Manim code
- 📚 View and manage your previous visualization projects

## System Requirements

- Python 3.8+
- Manim animation engine
- FFmpeg for video handling
- Anthropic API key (Claude 3.5)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/genimation.git
cd genimation
```

2. Create a virtual environment and activate it:
```bash
python -m venv env
source env/bin/activate  # On Windows, use: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `config.ini` file with your Anthropic API key:
```ini
[ANTHROPIC]
API_TOKEN=your_anthropic_api_key_here
```

## Usage

1. Start the FastAPI backend:
```bash
python main.py
```

2. In a separate terminal, start the Streamlit frontend:
```bash
streamlit run app.py
```

3. Open your browser and navigate to http://localhost:8501

## How It Works

1. Enter a mathematical topic or expression in the web interface
2. The system uses Claude AI to generate Manim code for visualizing the concept
3. The Manim code is executed to render a video animation
4. The resulting visualization is streamed to your browser

## Project Structure

- `main.py`: FastAPI backend server handling code generation and video rendering
- `app.py`: Streamlit frontend providing user interface
- `media/videos/`: Directory for temporary video files
- `videos/`: Directory for storing final rendered videos

## Credits

- Built with [Manim](https://github.com/ManimCommunity/manim) - Mathematical Animation Engine
- Powered by Claude AI from Anthropic
- Frontend created with Streamlit
- Backend powered by FastAPI