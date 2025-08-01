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
        self.root.geometry("500x700")
        self.root.minsize(400, 500)
        
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
        
        # Neumorphic & Minimalist color palette
        self.colors = {
            'bg': '#e6e7ee',           # Soft grey background
            'surface': '#e6e7ee',      # Same as background for seamless look
            'primary': '#667eea',      # Soft blue primary
            'accent': '#764ba2',       # Purple accent
            'text_primary': '#2d3748', # Dark grey text
            'text_secondary': '#718096', # Lighter grey text
            'shadow_dark': '#c8c9d0',  # Dark shadow for neumorphism
            'shadow_light': '#ffffff', # Light shadow for neumorphism
            'success': '#48bb78',      # Green for success states
            'warning': '#ed8936',      # Orange for warning states
        }
        
        # Set root background
        self.root.configure(bg=self.colors['bg'])
        
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
        
        # Create GUI
        self.create_widgets()
        
        # Bind keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.toggle_timer())
        self.root.bind('<space>', lambda e: self.toggle_timer())
        self.root.bind('<Escape>', lambda e: self.reset_timer())
        self.root.bind('<Right>', lambda e: self.skip_session())  # New skip shortcut
        
        # Make window focusable for keyboard events
        self.root.focus_set()
        
    def create_neumorphic_frame(self, parent, width=None, height=None, **kwargs):
        """Create a neumorphic style frame with soft shadows"""
        # Outer frame for shadow effect
        outer_frame = tk.Frame(
            parent,
            bg=self.colors['bg'],
            **kwargs
        )
        
        # Inner frame with raised appearance
        inner_frame = tk.Frame(
            outer_frame,
            bg=self.colors['surface'],
            relief='flat',
            bd=0
        )
        
        if width and height:
            inner_frame.configure(width=width, height=height)
            inner_frame.pack_propagate(False)
        
        inner_frame.pack(padx=8, pady=8)
        
        return outer_frame, inner_frame
    
    def create_neumorphic_button(self, parent, text, command, style="normal", **kwargs):
        """Create a neumorphic style button"""
        # Button colors based on style
        if style == "primary":
            bg_color = self.colors['primary']
            fg_color = 'white'
            active_bg = '#5a6fd8'
        elif style == "success":
            bg_color = self.colors['success']
            fg_color = 'white'
            active_bg = '#38a169'
        elif style == "warning":
            bg_color = self.colors['warning']
            fg_color = 'white'
            active_bg = '#dd7324'
        else:
            bg_color = self.colors['surface']
            fg_color = self.colors['text_primary']
            active_bg = '#dfe0e7'
        
        # Create button with neumorphic effect
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            activebackground=active_bg,
            activeforeground=fg_color if style in ["primary", "success", "warning"] else self.colors['text_primary'],
            font=("Arial", 12, "normal") if style == "normal" else ("Arial", 14, "bold"),
            relief='flat',
            bd=0,
            padx=24,
            pady=12,
            cursor="hand2",
            **kwargs
        )
        
        # Add hover effects
        def on_enter(e):
            if style == "primary":
                button.config(bg='#5a6fd8')
            elif style == "success":
                button.config(bg='#38a169')
            elif style == "warning":
                button.config(bg='#dd7324')
            else:
                button.config(bg='#dfe0e7')
        
        def on_leave(e):
            button.config(bg=bg_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
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
        """Create the main GUI elements with neumorphic & minimalist design"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Header - minimalist title
        header_frame = tk.Frame(main_container, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 40))
        
        title_label = tk.Label(
            header_frame,
            text="Pomodoro",
            font=("Arial", 28, "normal"),
            bg=self.colors['bg'],
            fg=self.colors['text_primary']
        )
        title_label.pack()
        
        # Session indicator - minimal
        self.session_label = tk.Label(
            header_frame,
            text=self.get_session_display_name(),
            font=("Arial", 16, "normal"),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.session_label.pack(pady=(5, 0))
        
        # Timer display - neumorphic card
        timer_outer, timer_inner = self.create_neumorphic_frame(main_container, width=320, height=180)
        timer_outer.pack(pady=(0, 40))
        
        self.time_display = tk.Label(
            timer_inner,
            text=self.format_time(self.time_remaining),
            font=("Arial", 52, "normal"),
            bg=self.colors['surface'],
            fg=self.colors['text_primary']
        )
        self.time_display.pack(expand=True)
        
        # Progress indicator (optional minimalist element)
        progress_frame = tk.Frame(main_container, bg=self.colors['bg'])
        progress_frame.pack(fill=tk.X, pady=(0, 30))
        
        self.progress_label = tk.Label(
            progress_frame,
            text=f"Session {self.session_count + 1}",
            font=("Arial", 12, "normal"),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.progress_label.pack()
        
        # Control buttons - minimalist layout
        controls_frame = tk.Frame(main_container, bg=self.colors['bg'])
        controls_frame.pack(pady=(0, 30))
        
        # Main action button (larger, primary)
        self.main_action_btn = self.create_neumorphic_button(
            controls_frame,
            "Start",
            self.toggle_timer,
            style="primary"
        )
        self.main_action_btn.pack(pady=(0, 16))
        
        # Secondary controls (smaller, in a row)
        secondary_frame = tk.Frame(controls_frame, bg=self.colors['bg'])
        secondary_frame.pack()
        
        self.pause_btn = self.create_neumorphic_button(
            secondary_frame,
            "Pause",
            self.pause_timer
        )
        self.pause_btn.pack(side=tk.LEFT, padx=8)
        self.pause_btn.config(state="disabled")
        
        self.reset_btn = self.create_neumorphic_button(
            secondary_frame,
            "Reset",
            self.reset_timer
        )
        self.reset_btn.pack(side=tk.LEFT, padx=8)
        
        # NEW: Skip button
        self.skip_btn = self.create_neumorphic_button(
            secondary_frame,
            "Skip",
            self.skip_session,
            style="warning"
        )
        self.skip_btn.pack(side=tk.LEFT, padx=8)
        
        # Settings - minimal icon button
        settings_frame = tk.Frame(main_container, bg=self.colors['bg'])
        settings_frame.pack(pady=(20, 0))
        
        self.settings_btn = self.create_neumorphic_button(
            settings_frame,
            "Settings",
            self.open_settings
        )
        self.settings_btn.pack()
    
    def get_session_display_name(self):
        """Get display name for current session type"""
        names = {
            "work": "Focus Time",
            "short_break": "Short Break",
            "long_break": "Long Break"
        }
        return names.get(self.current_session, "Focus Time")
    
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
        self.main_action_btn.config(text="Running...", state="disabled")
        self.pause_btn.config(state="normal")
        self.countdown()
    
    def pause_timer(self):
        """Pause the timer"""
        self.is_running = False
        self.is_paused = True
        self.main_action_btn.config(text="Resume", state="normal")
        self.pause_btn.config(state="disabled")
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
    
    def resume_timer(self):
        """Resume the paused timer"""
        self.is_running = True
        self.is_paused = False
        self.main_action_btn.config(text="Running...", state="disabled")
        self.pause_btn.config(state="normal")
        self.countdown()
    
    def reset_timer(self):
        """Reset the timer to the beginning of current session"""
        self.is_running = False
        self.is_paused = False
        self.main_action_btn.config(text="Start", state="normal")
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
    
    def skip_session(self):
        """NEW: Skip current session and move to next"""
        if self.is_running:
            # Stop current timer
            self.is_running = False
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
        
        # Show confirmation for skipping
        session_name = self.get_session_display_name()
        if messagebox.askyesno("Skip Session", f"Skip current {session_name}?"):
            # Move to next session
            self.next_session()
            
            # Reset button states
            self.main_action_btn.config(text="Start", state="normal")
            self.pause_btn.config(state="disabled")
            self.is_paused = False
            
            # Update display
            self.update_display()
            
            # Show notification
            next_session = self.get_session_display_name()
            messagebox.showinfo("Session Skipped", f"Moved to: {next_session}")
    
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
        self.main_action_btn.config(text="Start", state="normal")
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
            self.progress_label.config(text=f"Session {self.session_count + 1}")
            
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
        """Open modal settings dialog with neumorphic design"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x550")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.colors['bg'])
        settings_window.grab_set()  # Make it modal
        
        # Center the window
        settings_window.transient(self.root)
        x = (settings_window.winfo_screenwidth() // 2) - (300)
        y = (settings_window.winfo_screenheight() // 2) - (275)
        settings_window.geometry(f"600x550+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(settings_window, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            main_container,
            text="Settings",
            font=("Arial", 24, "normal"),
            bg=self.colors['bg'],
            fg=self.colors['text_primary']
        )
        title_label.pack(pady=(0, 30))
        
        # Settings card
        settings_outer, settings_inner = self.create_neumorphic_frame(main_container)
        settings_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Duration settings
        duration_label = tk.Label(
            settings_inner,
            text="Duration (minutes)",
            font=("Arial", 16, "normal"),
            bg=self.colors['surface'],
            fg=self.colors['text_primary']
        )
        duration_label.pack(anchor='w', pady=(20, 15), padx=20)
        
        # Input fields
        work_var = self.create_minimal_input(settings_inner, "Focus Time:", self.settings["work_duration"])
        short_var = self.create_minimal_input(settings_inner, "Short Break:", self.settings["short_break"])
        long_var = self.create_minimal_input(settings_inner, "Long Break:", self.settings["long_break"])
        sessions_var = self.create_minimal_input(settings_inner, "Sessions until Long Break:", self.settings["sessions_until_long_break"])
        
        # Sound settings
        sound_label = tk.Label(
            settings_inner,
            text="Notification Sound",
            font=("SF Pro Display", 16, "normal"),
            bg=self.colors['surface'],
            fg=self.colors['text_primary']
        )
        sound_label.pack(anchor='w', pady=(20, 15), padx=20)
        
        # Sound selection
        sound_frame = tk.Frame(settings_inner, bg=self.colors['surface'])
        sound_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.sound_var = tk.StringVar(value=self.settings.get("notification_sound", "Default"))
        
        browse_btn = self.create_neumorphic_button(
            sound_frame,
            "Choose Sound File",
            lambda: self.browse_sound_file()
        )
        browse_btn.pack(anchor='w')
        
        # Action buttons
        button_frame = tk.Frame(main_container, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X)
        
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
                messagebox.showinfo("Settings", "Settings saved successfully!")
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid positive numbers.")
        
        # Buttons
        save_btn = self.create_neumorphic_button(
            button_frame,
            "Save Settings",
            save_settings,
            style="success"
        )
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = self.create_neumorphic_button(
            button_frame,
            "Cancel",
            settings_window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def create_minimal_input(self, parent, label_text, default_value):
        """Create a minimal input field"""
        container = tk.Frame(parent, bg=self.colors['surface'])
        container.pack(fill=tk.X, padx=20, pady=8)
        
        label = tk.Label(
            container,
            text=label_text,
            font=("SF Pro Display", 12, "normal"),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary'],
            width=25,
            anchor='w'
        )
        label.pack(side=tk.LEFT)
        
        var = tk.StringVar(value=str(default_value))
        entry = tk.Entry(
            container,
            textvariable=var,
            font=("SF Pro Display", 12, "normal"),
            bg='white',
            fg=self.colors['text_primary'],
            relief='flat',
            bd=1,
            width=8
        )
        entry.pack(side=tk.RIGHT)
        
        return var
    
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
                
                messagebox.showinfo("Sound Selected", f"Sound file saved!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not copy sound file:\n{str(e)}")

    def handle_first_run(self):
        """Prompt user to select sound file if first time running"""
        if not self.settings.get("notification_sound"):
            answer = messagebox.askyesno("Setup", "Would you like to set a custom notification sound?")
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
                        messagebox.showinfo("Setup Complete", "Notification sound configured!")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not save sound:\n{str(e)}")

def main():
    """Main function to run the Pomodoro Timer application"""
    root = tk.Tk()
    app = PomodoroTimer(root)
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Exit Pomodoro Timer?"):
            pygame.mixer.quit()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()