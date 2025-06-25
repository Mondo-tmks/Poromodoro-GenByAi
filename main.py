import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import pygame
import threading
import time
from pathlib import Path
import shutil

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.geometry("500x600")
        self.root.minsize(300, 200)
        self.root.configure(bg="#f9f9f9")  # Light background
        
        # Load application icon if it exists
        try:
            self.root.iconbitmap("assets/app_icon.ico")
        except:
            pass  # Icon file not found, continue without it
        
        # Initialize pygame mixer for sound
        try:
            pygame.mixer.init()
        except:
            print("Warning: Could not initialize audio system")
        
        # Bright & Light color palette
        self.colors = {
            'bg': '#f9f9f9',           # Light background
            'primary': '#ff6f61',      # Warm tomato accent
            'button_bg': '#ffffff',    # White buttons
            'button_hover': '#ffe6e1', # Light pink hover
            'text': '#333333',         # Dark text
            'timer_text': '#444444',   # Timer display
            'shadow': '#e0e0e0'        # Soft shadow
        }
        
        # Configuration file path
        self.config_file = "pomodoro_config.json"
        
        # Create assets directory if it doesn't exist
        self.assets_dir = Path("assets")
        self.assets_dir.mkdir(exist_ok=True)
        
        # Default settings
        self.default_settings = {
            "work_duration": 25,  # minutes
            "short_break": 5,     # minutes
            "long_break": 15,     # minutes
            "sessions_until_long_break": 4,
            "notification_sound": ""  # Path to custom sound file
        }
        
        # Load settings
        self.settings = self.load_settings()
        self.handle_first_run()
        
        # Timer state variables
        self.current_session = "work"  # work, short_break, long_break
        self.session_count = 0
        self.time_remaining = self.settings["work_duration"] * 60  # seconds
        self.is_running = False
        self.is_paused = False
        self.timer_job = None
        
        # Configure styles
        self.configure_styles()
        
        # Create GUI
        self.create_widgets()
        
        # Configure tab order for accessibility
        self.configure_tab_order()
        
        # Bind keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.toggle_timer())
        self.root.bind('<space>', lambda e: self.toggle_timer())
        self.root.bind('<Escape>', lambda e: self.reset_timer())
        
        # Make window focusable for keyboard events
        self.root.focus_set()
        
    def configure_styles(self):
        """Configure custom styles for ttk widgets"""
        style = ttk.Style()
        
        # Configure button style with rounded appearance
        style.configure(
            "Rounded.TButton",
            background=self.colors['button_bg'],
            foreground=self.colors['text'],
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            borderwidth=1,
            focuscolor="none",
            padding=(20, 10)
        )
        
        # Configure button hover effects
        style.map(
            "Rounded.TButton",
            background=[('active', self.colors['button_hover']),
                       ('pressed', self.colors['button_hover'])],
            relief=[('pressed', 'flat')]
        )
        
        # Configure primary button style
        style.configure(
            "Primary.TButton",
            background=self.colors['primary'],
            foreground="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            borderwidth=0,
            focuscolor="none",
            padding=(25, 12)
        )
        
        style.map(
            "Primary.TButton",
            background=[('active', '#ff5a4d'),
                       ('pressed', '#ff5a4d')]
        )
        
        # Configure label styles
        style.configure(
            "Header.TLabel",
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=("Segoe UI", 18, "bold")
        )
        
        style.configure(
            "Timer.TLabel",
            background=self.colors['bg'],
            foreground=self.colors['timer_text'],
            font=("Segoe UI", 48, "bold")
        )
        
        style.configure(
            "Status.TLabel",
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=("Segoe UI", 12)
        )
        
        style.configure(
            "Small.TLabel",
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=("Segoe UI", 9)
        )
        
    def load_settings(self):
        """Load settings from JSON file or create default settings"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Ensure all default keys exist
                    for key in self.default_settings:
                        if key not in loaded_settings:
                            loaded_settings[key] = self.default_settings[key]
                    return loaded_settings
            else:
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
        except Exception:
            return self.default_settings.copy()
    
    def save_settings(self, settings):
        """Save settings to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass
    
    def create_widgets(self):
        """Create the main GUI elements with bright & light theme"""
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=0)  # Header
        self.root.grid_rowconfigure(1, weight=1)  # Timer
        self.root.grid_rowconfigure(2, weight=0)  # Controls
        self.root.grid_rowconfigure(3, weight=0)  # Settings
        self.root.grid_columnconfigure(0, weight=1)
        
        # Header Label
        header_label = ttk.Label(
            self.root,
            text="Pomodoro Timer",
            style="Header.TLabel"
        )
        header_label.grid(row=0, column=0, pady=(20, 10))
        
        # Timer Display (Large Font) - centered
        timer_frame = tk.Frame(self.root, bg=self.colors['bg'])
        timer_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        timer_frame.grid_rowconfigure(0, weight=1)
        timer_frame.grid_columnconfigure(0, weight=1)
        
        # Create timer display with soft background
        timer_bg_frame = tk.Frame(
            timer_frame, 
            bg="white",
            relief="flat",
            bd=1
        )
        timer_bg_frame.grid(row=0, column=0, sticky="", padx=20, pady=20)
        
        self.time_display = ttk.Label(
            timer_bg_frame,
            text=self.format_time(self.time_remaining),
            style="Timer.TLabel",
            background="white"
        )
        self.time_display.pack(padx=40, pady=30)
        
        # Session indicator
        self.session_label = ttk.Label(
            timer_frame,
            text=self.get_session_display_name(),
            style="Status.TLabel"
        )
        self.session_label.grid(row=1, column=0, pady=(0, 10))
        
        # Control Buttons - horizontal layout
        control_frame = tk.Frame(self.root, bg=self.colors['bg'])
        control_frame.grid(row=2, column=0, pady=20)
        
        # Start/Pause button (primary)
        self.start_pause_btn = ttk.Button(
            control_frame,
            text="Start",
            command=self.toggle_timer,
            style="Primary.TButton"
        )
        self.start_pause_btn.grid(row=0, column=0, padx=5)
        self.start_pause_btn.configure(cursor="hand2")
        
        # Pause button (separate for clarity)
        self.pause_btn = ttk.Button(
            control_frame,
            text="Pause",
            command=self.pause_timer,
            style="Rounded.TButton",
            state="disabled"
        )
        self.pause_btn.grid(row=0, column=1, padx=5)
        self.pause_btn.configure(cursor="hand2")
        
        # Reset button
        self.reset_btn = ttk.Button(
            control_frame,
            text="Reset",
            command=self.reset_timer,
            style="Rounded.TButton"
        )
        self.reset_btn.grid(row=0, column=2, padx=5)
        self.reset_btn.configure(cursor="hand2")
        
        # Settings button with gear icon
        settings_frame = tk.Frame(self.root, bg=self.colors['bg'])
        settings_frame.grid(row=3, column=0, pady=(0, 20))
        
        self.settings_btn = ttk.Button(
            settings_frame,
            text="Settings ⚙",
            command=self.open_settings,
            style="Rounded.TButton"
        )
        self.settings_btn.pack()
        self.settings_btn.configure(cursor="hand2")
        
        # Session counter (small text)
        self.session_counter_label = ttk.Label(
            self.root,
            text=f"Sessions completed: {self.session_count}",
            style="Small.TLabel"
        )
        self.session_counter_label.grid(row=4, column=0, pady=(0, 10))
        
        # Add tooltips for accessibility
        self.add_tooltips()
    
    def add_tooltips(self):
        """Add tooltips to buttons for accessibility"""
        def create_tooltip(widget, text):
            def on_enter(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = tk.Label(
                    tooltip, 
                    text=text,
                    background="#ffffe0",
                    relief="solid",
                    borderwidth=1,
                    font=("Segoe UI", 9)
                )
                label.pack()
                widget.tooltip = tooltip
            
            def on_leave(event):
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    del widget.tooltip
            
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        create_tooltip(self.start_pause_btn, "Start the timer (Enter/Space)")
        create_tooltip(self.pause_btn, "Pause the current session")
        create_tooltip(self.reset_btn, "Reset timer to beginning (Escape)")
        create_tooltip(self.settings_btn, "Configure timer settings")
    
    def configure_tab_order(self):
        """Configure tab order for keyboard navigation"""
        widgets = [
            self.start_pause_btn,
            self.pause_btn, 
            self.reset_btn,
            self.settings_btn
        ]
        
        for i, widget in enumerate(widgets):
            widget.bind("<Tab>", lambda e, next_widget=widgets[(i+1) % len(widgets)]: next_widget.focus())
    
    def get_session_display_name(self):
        """Get display name for current session type"""
        names = {
            "work": "Work Session",
            "short_break": "Short Break",
            "long_break": "Long Break"
        }
        return names.get(self.current_session, "Work Session")
    
    def format_time(self, seconds):
        """Format seconds into MM:SS format"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def toggle_timer(self):
        """Start or resume the timer"""
        if not self.is_running and not self.is_paused:
            self.start_timer()
        elif self.is_paused:
            self.resume_timer()
    
    def start_timer(self):
        """Start the timer"""
        self.is_running = True
        self.is_paused = False
        self.start_pause_btn.config(text="Running...", state="disabled")
        self.pause_btn.config(state="normal")
        self.countdown()
    
    def pause_timer(self):
        """Pause the timer"""
        self.is_running = False
        self.is_paused = True
        self.start_pause_btn.config(text="Resume", state="normal")
        self.pause_btn.config(state="disabled")
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
    
    def resume_timer(self):
        """Resume the paused timer"""
        self.is_running = True
        self.is_paused = False
        self.start_pause_btn.config(text="Running...", state="disabled")
        self.pause_btn.config(state="normal")
        self.countdown()
    
    def reset_timer(self):
        """Reset the timer to the beginning of current session"""
        self.is_running = False
        self.is_paused = False
        self.start_pause_btn.config(text="Start", state="normal")
        self.pause_btn.config(state="disabled")
        
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
        
        # Reset time based on current session
        if self.current_session == "work":
            self.time_remaining = self.settings["work_duration"] * 60
        elif self.current_session == "short_break":
            self.time_remaining = self.settings["short_break"] * 60
        else:  # long_break
            self.time_remaining = self.settings["long_break"] * 60
        
        self.update_display()
    
    def countdown(self):
        """Main countdown logic"""
        if self.is_running and self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_display()
            self.timer_job = self.root.after(1000, self.countdown)
        elif self.time_remaining == 0:
            self.session_complete()
    
    def session_complete(self):
        """Handle session completion"""
        self.is_running = False
        self.start_pause_btn.config(text="Start", state="normal")
        self.pause_btn.config(state="disabled")
        
        # Play notification sound
        self.play_notification_sound()
        
        # Show completion notification
        session_name = self.get_session_display_name()
        messagebox.showinfo("Session Complete", f"{session_name} completed!\n\nGreat work! 🎉")
        
        # Move to next session
        self.next_session()
        self.update_display()
    
    def play_notification_sound(self):
        """Play notification sound for 5 seconds maximum"""
        def play_sound():
            try:
                sound_file = self.settings.get("notification_sound", "")
                if sound_file and os.path.exists(sound_file):
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.play()
                    # Stop after 5 seconds
                    threading.Timer(5.0, pygame.mixer.music.stop).start()
                else:
                    # Fallback: system beep
                    self.root.bell()
            except Exception:
                # Fallback: system beep
                self.root.bell()
        
        # Play in separate thread to avoid blocking UI
        threading.Thread(target=play_sound, daemon=True).start()
    
    def next_session(self):
        """Move to the next session type"""
        if self.current_session == "work":
            self.session_count += 1
            self.session_counter_label.config(text=f"Sessions completed: {self.session_count}")
            
            # Check if it's time for long break
            if self.session_count % self.settings["sessions_until_long_break"] == 0:
                self.current_session = "long_break"
                self.time_remaining = self.settings["long_break"] * 60
            else:
                self.current_session = "short_break"
                self.time_remaining = self.settings["short_break"] * 60
        else:
            # Break finished, back to work
            self.current_session = "work"
            self.time_remaining = self.settings["work_duration"] * 60
        
        self.session_label.config(text=self.get_session_display_name())
    
    def update_display(self):
        """Update the time display"""
        self.time_display.config(text=self.format_time(self.time_remaining))
    
    def open_settings(self):
        """Open modal settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("700x500")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.colors['bg'])
        settings_window.grab_set()  # Make it modal
        
        # Center the window
        settings_window.transient(self.root)
        x = (settings_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (400 // 2)
        settings_window.geometry(f"700x500+{x}+{y}")
        
        # Main frame with padding
        main_frame = tk.Frame(settings_window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Timer Settings",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=(0, 20))
        
        # Settings frame
        settings_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Duration settings
        duration_label = tk.Label(
            settings_frame,
            text="Duration Settings (minutes)",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        duration_label.pack(anchor='w', pady=(0, 10))
        
        # Work duration
        work_frame = self.create_input_field(settings_frame, "Work Duration:", 
                                           self.settings["work_duration"])
        work_var = work_frame[1]
        
        # Short break
        short_frame = self.create_input_field(settings_frame, "Short Break:", 
                                            self.settings["short_break"])
        short_var = short_frame[1]
        
        # Long break
        long_frame = self.create_input_field(settings_frame, "Long Break:", 
                                           self.settings["long_break"])
        long_var = long_frame[1]
        
        # Sessions until long break
        sessions_frame = self.create_input_field(settings_frame, "Sessions until Long Break:", 
                                               self.settings["sessions_until_long_break"])
        sessions_var = sessions_frame[1]
        
        # Sound settings
        sound_label = tk.Label(
            settings_frame,
            text="Notification Sound",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        sound_label.pack(anchor='w', pady=(20, 10))
        
        # Sound file selection
        sound_frame = tk.Frame(settings_frame, bg=self.colors['bg'])
        sound_frame.pack(fill=tk.X, pady=5)
        
        self.sound_var = tk.StringVar(value=self.settings.get("notification_sound", "Default beep"))
        sound_display = tk.Label(
            sound_frame,
            textvariable=self.sound_var,
            font=("Segoe UI", 10),
            bg="white",
            fg=self.colors['text'],
            relief="sunken",
            bd=1,
            anchor='w'
        )
        sound_display.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(
            sound_frame,
            text="Browse...",
            command=lambda: self.browse_sound_file(),
            bg=self.colors['button_bg'],
            fg=self.colors['text'],
            font=("Segoe UI", 10),
            relief="flat",
            bd=1,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.RIGHT)
        
        def save_settings():
            try:
                new_settings = {
                    "work_duration": int(work_var.get()),
                    "short_break": int(short_var.get()),
                    "long_break": int(long_var.get()),
                    "sessions_until_long_break": int(sessions_var.get()),
                    "notification_sound": self.settings.get("notification_sound", "")
                }
                
                # Validate settings
                for key, value in new_settings.items():
                    if key != "notification_sound" and value <= 0:
                        raise ValueError(f"{key} must be positive")
                
                self.settings = new_settings
                self.save_settings(self.settings)
                
                # Reset current timer if not running
                if not self.is_running:
                    self.reset_timer()
                
                settings_window.destroy()
                messagebox.showinfo("Settings", "Settings saved successfully! ✓")
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", "Please enter valid positive numbers for all duration fields.")
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Save button (primary)
        save_btn = tk.Button(
            button_frame,
            text="Save Settings",
            command=save_settings,
            bg=self.colors['primary'],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=25,
            pady=10,
            cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=settings_window.destroy,
            bg=self.colors['button_bg'],
            fg=self.colors['text'],
            font=("Segoe UI", 11),
            relief="flat",
            bd=1,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def create_input_field(self, parent, label_text, default_value):
        """Create an input field with validation"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(
            frame,
            text=label_text,
            font=("Segoe UI", 11),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            width=25,
            anchor='w'
        )
        label.pack(side=tk.LEFT)
        
        var = tk.StringVar(value=str(default_value))
        entry = tk.Entry(
            frame,
            textvariable=var,
            font=("Segoe UI", 11),
            bg="white",
            fg=self.colors['text'],
            relief="flat",
            bd=1,
            width=10
        )
        entry.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add validation
        def validate_input(event):
            try:
                value = int(var.get())
                if value > 0:
                    entry.config(bg="white")
                else:
                    entry.config(bg="#ffe6e6")
            except ValueError:
                entry.config(bg="#ffe6e6")
        
        entry.bind("<KeyRelease>", validate_input)
        
        return frame, var
    
    def browse_sound_file(self):
        """Open file dialog to select notification sound"""
        filetypes = [
            ("Audio files", "*.wav *.mp3"),
            ("WAV files", "*.wav"),
            ("MP3 files", "*.mp3"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Notification Sound",
            filetypes=filetypes,
            initialdir=os.path.expanduser("~")
        )
        
        if filename:
            try:
                # Copy file to assets directory
                target_path = self.assets_dir / f"notification{Path(filename).suffix}"
                shutil.copy2(filename, target_path)
                
                # Update settings
                self.settings["notification_sound"] = str(target_path)
                self.sound_var.set(f"Custom: {Path(filename).name}")
                
                messagebox.showinfo("Sound Selected", f"Sound file copied to:\n{target_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not copy sound file:\n{str(e)}")


    def handle_first_run(self):
        """Prompt user to select sound file if first time running"""
        if not self.settings.get("notification_sound"):
            answer = messagebox.askyesno("Setup Notification Sound", "Would you like to upload a custom notification sound?")
            if answer:
                filetypes = [
                    ("Audio files", "*.wav *.mp3"),
                    ("WAV files", "*.wav"),
                    ("MP3 files", "*.mp3"),
                    ("All files", "*.*")
                ]
                filename = filedialog.askopenfilename(
                    title="Select Notification Sound",
                    filetypes=filetypes,
                    initialdir=os.path.expanduser("~")
                )
                if filename:
                    try:
                        target_path = self.assets_dir / f"user_notify{Path(filename).suffix}"
                        shutil.copy2(filename, target_path)
                        self.settings["notification_sound"] = str(target_path)
                        self.save_settings(self.settings)
                        messagebox.showinfo("Sound Set", f"Notification sound saved to: {target_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not save notification sound:\n{str(e)}")

def main():
    """Main function to run the Pomodoro Timer application"""
    root = tk.Tk()
    app = PomodoroTimer(root)
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit the Pomodoro Timer?"):
            pygame.mixer.quit()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()