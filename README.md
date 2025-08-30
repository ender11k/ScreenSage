# ScreenSage
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 🖥️ Screen Q&A Assistant  

An **AI-powered desktop assistant for Windows** that overlays on your screen with transparency, lets you capture text using OCR, and get instant answers powered by **Google Gemini API**.  
The app supports structured answers, draggable/resizable panels, and syntax highlighting for code snippets.  

---

## ✨ Features
- 🔍 **Screen OCR** – Capture text directly from your screen using Tesseract.  
- 🤖 **AI Integration** – Get instant answers powered by Gemini.  
- 🪟 **Modern Overlay UI** – Frameless, draggable, and resizable panels with smooth styling.  
- 💬 **Structured Answers** – ChatGPT-like formatted responses inside an answer panel.  
- 🎨 **Code Syntax Highlighting** – Automatically formats and highlights code in responses.  
- ⚡ **System Tray Integration** – Runs in background with quick access.  
- ❌ **Easy Exit** – Quit anytime using the overlay close button or tray menu.  

---

## 🚀 Installation

### 1. Clone the repo
```bash
git clone https://github.com/your-username/screen-qa-assistant.git
cd screen-qa-assistant
```
### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your API key

In your code, replace:
```bash
genai.configure(api_key="YOUR_GEMINI_API_KEY")
```

with your actual Gemini API key.

### 5. Run the app
```bash
python main.py
```

### 🛠️ Build as .exe

If you want to package the app into a standalone .exe:
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile main.py
```

The .exe will appear inside the dist/ folder.

### 📦 Requirements

- Python 3.9+
- PySide6
- pytesseract & Tesseract OCR installed on system
- mss for screen capture
- google-generativeai for Gemini API

Install all at once:
```bash
pip install PySide6 pytesseract pillow mss google-generativeai pygments
```
### 📷 Screenshots
<img width="366" height="292" alt="Screenshot 2025-08-30 115530" src="https://github.com/user-attachments/assets/b1a746c5-24bf-4292-bbf3-271eaba8b1c8" />
<img width="1365" height="743" alt="Screenshot 2025-08-30 115604" src="https://github.com/user-attachments/assets/3d0e82ab-7d9d-4495-8484-d2ad02039afb" />

### 🧑‍💻 Contributing

PRs are welcome! Feel free to fork the repo and submit improvements for UI, features, or integrations.

### ⚖️ License

MIT License © 2025 Yash Samarth

### 🙌 Acknowledgements

- Google Gemini API
- Tesseract OCR
- PySide6

