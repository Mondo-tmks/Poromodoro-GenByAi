
# Pomodoro Timer Desktop Application

### CRAFTED THIS APP FOR 20MINUTES FROM CHATGPT AS PLANNER & CLUADE AS CODER

A kinda Havy weight, ugly-themed Pomodoro Timer desktop application built with Python and Tkinter, designed for Windows 7+.

## 🎯 Features

- Start, pause, reset Pomodoro timer
- Customizable session durations (work, short/long break)
- Stupid % Ugly UI with responsive layout
- First-run prompt for uploading your own notification sound (.wav or .mp3)
- Standalone executable generated with PyInstaller
- Optional packaging using Inno Setup for professional installers

## 💻 Requirements

- Python 3.8.6 (recommended for Windows 7 compatibility)
- pip (Python package manager)

## 📁 Project Structure

```
PomodoroApp/
├── main.py                 # Main application script
├── assets/                 # App icon and default notification sounds
│   └── app_icon.ico
│   └── default_notify.wav
├── user_data/              # Stores custom sound and config on first run
│   └── config.json
│   └── sounds/
└── requirements.txt        # List of required packages
```

## 🚀 Getting Started

### 1. Clone this repository

```bash
git clone https://github.com/yourusername/PomodoroTimer.git
cd PomodoroTimer
```

### 2. Set up your virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python main.py
```

On first launch, you’ll be prompted to upload a custom notification sound (optional).

## 📦 Build Executable

Using PyInstaller:

```bash
pyinstaller main.py --onefile --windowed --icon=assets\app_icon.ico --name PomodoroTimer
```

Your EXE will be located at `dist/PomodoroTimer.exe`.

## 🛠 Optional Installer (Inno Setup)

To create a traditional Windows installer:

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Open `installer.iss` in Inno Setup Compiler
3. Click **Compile**
4. Output: `PomodoroSetup.exe`

## 📝 License

MIT License

---

*Created with 💡 for focused work sessions.*
