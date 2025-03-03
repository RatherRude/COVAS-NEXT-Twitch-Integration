import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import json
import os
import subprocess
import sys
import threading
import queue
import io
from contextlib import redirect_stdout
from typing import Dict, Any, cast, Optional, Union
from twitch import DEFAULT_CONFIG, load_or_create_config, main as twitch_main
from EDMesg.base import EDMesgEvent
from EDMesg.TwitchIntegration import create_twitch_provider, TwitchNotificationEvent

class ConfigManager:
    def __init__(self, root):
        self.root = root
        self.root.title("COVAS:NEXT Twitch Integration")
        
        # Initialize instance variables
        self.container: Optional[tk.Frame] = None
        self.bot_process = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None
        self.main_container: Optional[ttk.Frame] = None
        self.log_container: Optional[tk.Frame] = None
        self.output_queue: queue.Queue[Optional[str]] = queue.Queue()
        self.reading_thread: Optional[threading.Thread] = None
        self.should_stop = False
        self.config: Dict[str, Any] = {}
        self.pattern_entries: Dict[str, ttk.Entry] = {}
        self.instruction_entries: Dict[str, ttk.Entry] = {}
        self.twitch_provider = create_twitch_provider()  # Create Twitch provider
        
        # Set initial window size
        window_width = 800
        window_height = 600
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Create styles
        style = ttk.Style()
        style.configure('Transparent.TFrame', background='')
        style.configure('Transparent.TLabelframe', background='')
        style.configure('Transparent.TLabelframe.Label', background='')
        style.configure('SemiTransparent.TLabel', background='')
        style.configure('Visible.TButton', background='white')
        
        # Set window icon
        icon_path = os.path.join('assets', 'EDAI_logo_transparent.png')
        if os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, photo)
            except Exception as e:
                print(f"Error loading icon: {str(e)}")
        
        # Create a container frame
        self.container = tk.Frame(self.root)
        self.container.place(relwidth=1, relheight=1)
        
        # Load configuration
        self.config = load_or_create_config()
        
        # Create main container for settings
        self.main_container = ttk.Frame(self.container, padding="10", style='Transparent.TFrame')
        self.main_container.pack(fill='both', expand=True)
        
        # Create log container (initially hidden)
        self.log_container = tk.Frame(self.container, background='black')
        self.log_text = scrolledtext.ScrolledText(self.log_container, wrap=tk.WORD, bg='black', fg='purple')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        stop_button = ttk.Button(self.log_container, text="Stop Bot", command=self.stop_bot)
        stop_button.pack(pady=5)
        
        # Basic Settings
        self.setup_basic_settings(self.main_container)
        
        # Event Settings
        self.setup_event_settings(self.main_container)
        
        # Control Buttons
        self.setup_control_buttons(self.main_container)
        
        # Load existing values
        self.load_values()

    def setup_basic_settings(self, parent):
        # Basic Settings Frame with transparency
        basic_frame = ttk.LabelFrame(parent, text="Basic Settings", padding="5", style='Transparent.TLabelframe')
        basic_frame.pack(fill='x', padx=5, pady=5)
        
        # Channel Name
        ttk.Label(basic_frame, text="Twitch Channel:", background='').pack(anchor='w')
        self.channel_entry = ttk.Entry(basic_frame)
        self.channel_entry.pack(fill='x', padx=5, pady=2)
        
        # Bot Name
        ttk.Label(basic_frame, text="Bot Name:", background='').pack(anchor='w')
        self.bot_name_entry = ttk.Entry(basic_frame)
        self.bot_name_entry.pack(fill='x', padx=5, pady=2)

    def setup_event_settings(self, parent):
        # Event Settings Frame with transparency
        event_frame = ttk.LabelFrame(parent, text="Event Settings", padding="5", style='Transparent.TLabelframe')
        event_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbar for events
        canvas = tk.Canvas(event_frame, highlightthickness=0, bg='#F0F0F0')
        scrollbar = ttk.Scrollbar(event_frame, orient="vertical", command=canvas.yview)
        
        # Create styles for frames and labels
        style = ttk.Style()
        style.configure('Transparent.TFrame', background='#F0F0F0')
        style.configure('SemiTransparent.TLabel', background='#F0F0F0')
        
        # Create scrollable frame with style
        scrollable_frame = ttk.Frame(canvas, style='Transparent.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Event settings
        self.pattern_entries = {}
        self.instruction_entries = {}
        
        events = [
            ('follow', 'Follow', '{user}'),
            ('tip', 'Tip', '{user}, {amount}, message'),
            ('host', 'Host', '{user}, {viewers}'),
            ('sub', 'Subscribe', '{user}'),
            ('resub', 'Resub', '{user}, {months}'),
            ('giftsub', 'Gift Sub', '{user}'),
            ('bits', 'Bits', '{user}, {amount}, message'),
            ('redeem', 'Redeem', '{user}, {reward}'),
            ('raid', 'Raid', '{user}, {viewers}'),
            ('order', 'Order', '{user}, {item}')
        ]
        
        for i, (event_key, event_name, variables) in enumerate(events):
            # Event header with semi-transparent background
            label_frame = ttk.Frame(scrollable_frame, style='Transparent.TFrame')
            label_frame.grid(row=i*3, column=0, columnspan=2, sticky='ew', padx=5, pady=(10,0))
            
            ttk.Label(label_frame, text=f"{event_name}", font=('Helvetica', 10, 'bold'), style='SemiTransparent.TLabel').pack(side='left', padx=5)
            ttk.Label(label_frame, text=f"Example: {DEFAULT_CONFIG['patterns'][event_key]}", font=('Helvetica', 8), style='SemiTransparent.TLabel').pack(side='left', padx=5)
            
            # Pattern
            pattern_frame = ttk.Frame(scrollable_frame, style='Transparent.TFrame')
            pattern_frame.grid(row=i*3+1, column=0, columnspan=2, sticky='ew', padx=5)
            
            ttk.Label(pattern_frame, text="Pattern:", style='SemiTransparent.TLabel').pack(side='left', padx=5)
            self.pattern_entries[event_key] = ttk.Entry(pattern_frame, width=40)
            self.pattern_entries[event_key].pack(side='left', fill='x', expand=True, padx=5)
            
            # Instruction
            instruction_frame = ttk.Frame(scrollable_frame, style='Transparent.TFrame')
            instruction_frame.grid(row=i*3+2, column=0, columnspan=2, sticky='ew', padx=5)
            
            ttk.Label(instruction_frame, text="Instruction:", style='SemiTransparent.TLabel').pack(side='left', padx=5)
            self.instruction_entries[event_key] = ttk.Entry(instruction_frame, width=80)
            self.instruction_entries[event_key].pack(side='left', fill='x', expand=True, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_control_buttons(self, parent):
        button_frame = ttk.Frame(parent, style='Transparent.TFrame')
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Start Bot", command=self.start_bot, style='Visible.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults, style='Visible.TButton').pack(side='right', padx=5)

    def load_values(self):
        # Load basic settings
        if not isinstance(self.config, dict):
            self.config = DEFAULT_CONFIG.copy()
        
        # Get values with proper type checking
        channel = str(self.config.get('channel', ''))
        bot_name = str(self.config.get('bot_name', ''))
        self.channel_entry.insert(0, channel)
        self.bot_name_entry.insert(0, bot_name)
        
        # Load patterns and instructions with proper type checking
        config_patterns = self.config.get('patterns', {})
        config_instructions = self.config.get('instructions', {})
        
        patterns = cast(Dict[str, str], DEFAULT_CONFIG['patterns']).copy()
        instructions = cast(Dict[str, str], DEFAULT_CONFIG['instructions']).copy()
        
        if isinstance(config_patterns, dict):
            patterns.update(config_patterns)
        if isinstance(config_instructions, dict):
            instructions.update(config_instructions)
        
        for event_key in self.pattern_entries:
            default_patterns = cast(Dict[str, str], DEFAULT_CONFIG['patterns'])
            default_instructions = cast(Dict[str, str], DEFAULT_CONFIG['instructions'])
            
            pattern_value = str(patterns.get(event_key, default_patterns.get(event_key, '')))
            instruction_value = str(instructions.get(event_key, default_instructions.get(event_key, '')))
            self.pattern_entries[event_key].insert(0, pattern_value)
            self.instruction_entries[event_key].insert(0, instruction_value)

    def save_config(self):
        # Ensure config is a dictionary
        if not isinstance(self.config, dict):
            self.config = DEFAULT_CONFIG.copy()
        
        # Update config with current values
        self.config['channel'] = self.channel_entry.get()
        self.config['bot_name'] = self.bot_name_entry.get()
        
        # Initialize sections if they don't exist
        if 'patterns' not in self.config or not isinstance(self.config['patterns'], dict):
            self.config['patterns'] = {}
        if 'instructions' not in self.config or not isinstance(self.config['instructions'], dict):
            self.config['instructions'] = {}
        
        # Update patterns and instructions
        patterns = cast(Dict[str, str], self.config['patterns'])
        instructions = cast(Dict[str, str], self.config['instructions'])
        
        for event_key in self.pattern_entries:
            patterns[event_key] = self.pattern_entries[event_key].get()
            instructions[event_key] = self.instruction_entries[event_key].get()
        
        # Save to file
        try:
            with open('covas_twitch_config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Failed to save configuration: {str(e)}")

    def reset_to_defaults(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
            self.config = DEFAULT_CONFIG.copy()
            # Clear and reload all fields
            self.channel_entry.delete(0, tk.END)
            self.bot_name_entry.delete(0, tk.END)
            
            for entry in self.pattern_entries.values():
                entry.delete(0, tk.END)
            for entry in self.instruction_entries.values():
                entry.delete(0, tk.END)
            
            self.load_values()

    def read_output(self):
        """Read subprocess output in a separate thread"""
        while not self.should_stop and self.bot_process and self.bot_process.poll() is None:
            try:
                line = self.bot_process.stdout.readline()
                if line:
                    self.output_queue.put(line)
            except:
                break
        
        # Read any remaining output
        if self.bot_process and self.bot_process.poll() is not None:
            try:
                remaining = self.bot_process.stdout.read()
                if remaining:
                    self.output_queue.put(remaining)
            except:
                pass
        
        self.output_queue.put(None)  # Signal end of output

    def start_bot(self):
        # Get current values from entries
        channel = self.channel_entry.get().strip()
        bot_name = self.bot_name_entry.get().strip()
        
        if not channel or not bot_name:
            messagebox.showerror("Error", "Please enter both Channel Name and Bot Name before starting.")
            return
        
        # Update config with current values before saving
        self.config['channel'] = channel
        self.config['bot_name'] = bot_name
        
        # Auto-save configuration before starting
        self.save_config()
        
        # Hide main container and show log container
        main_container = self.main_container
        log_container = self.log_container
        log_text = self.log_text
        
        try:
            if isinstance(main_container, ttk.Frame):
                main_container.pack_forget()
            if isinstance(log_container, tk.Frame) and isinstance(log_text, scrolledtext.ScrolledText):
                log_container.pack(fill='both', expand=True)
                log_text.delete(1.0, tk.END)
                log_text.tag_configure("orange", foreground="orange")
                log_text.tag_configure("cyan", foreground="cyan")
                log_text.insert(tk.END, "Starting bot...\n", "orange")
                log_text.see(tk.END)
        except tk.TclError:
            # Handle case where widgets are already destroyed
            pass
        
        # Reset thread control
        self.should_stop = False
        
        # Start the bot as a subprocess
        try:
            config_str = json.dumps(self.config)
            
            # Determine if we're running from a PyInstaller bundle
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                bot_script = os.path.join(os.path.dirname(sys.executable), 'COVAS_Twitch_Bot.exe')
                if not os.path.exists(bot_script):
                    bot_script = 'COVAS_Twitch_Bot.exe'  # Try current directory
            else:
                # Running as script
                bot_script = 'twitch.py'
            
            if getattr(sys, 'frozen', False) and not os.path.exists(bot_script):
                error_msg = "Error: Could not find COVAS_Twitch_Bot.exe. Make sure it's in the same directory as the main executable.\n"
                if self.log_text is not None:
                    self.log_text.insert(tk.END, error_msg)
                    self.log_text.see(tk.END)
                self.stop_bot()
                return
            
            # Prepare command
            if bot_script.endswith('.py'):
                cmd = [sys.executable, bot_script]
            else:
                cmd = [bot_script]
            
            cmd.extend([
                '--channel',
                channel,
                '--bot-name',
                bot_name,
                '--patterns',
                config_str
            ])
            
            # Start bot process
            self.bot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Start output reading thread
            self.reading_thread = threading.Thread(target=self.read_output)
            self.reading_thread.daemon = True
            self.reading_thread.start()
            
            # Start updating log
            self.root.after(100, self.update_log)
            
        except Exception as e:
            error_msg = f"Error starting bot: {str(e)}\n"
            if self.log_text is not None:
                self.log_text.insert(tk.END, error_msg)
                self.log_text.see(tk.END)
            self.stop_bot()

    def update_log(self):
        """Update log with bot output"""
        try:
            # Process all available output
            while True:
                try:
                    line = self.output_queue.get_nowait()
                    if line is None:  # End of output
                        self.stop_bot()
                        return
                    if self.log_text is not None:
                        # Check if this is an INSTRUCTION entry
                        if isinstance(line, str) and "INSTRUCTION" in line:
                            self.log_text.insert(tk.END, line, "cyan")
                            # Send instruction to EDMesg using TwitchNotificationEvent
                            try:
                                # Parse the instruction line
                                instruction_text = line.replace("INSTRUCTION:", "").strip()
                                
                                # Extract timestamp if present
                                timestamp = ""
                                if line.startswith("[") and "]" in line:
                                    timestamp = line[1:line.index("]")]
                                
                                # Try to find the event type from the instruction text
                                event_type = None
                                for key in self.config.get('patterns', {}):
                                    if key in instruction_text.lower():
                                        event_type = key
                                        break
                                
                                # If we found the event type, combine pattern and instruction
                                if event_type and event_type in self.config.get('patterns', {}):
                                    pattern_text = self.config['patterns'][event_type]
                                    message = f"{pattern_text} | {instruction_text}"
                                else:
                                    message = instruction_text
                                
                                self.twitch_provider.publish(
                                    TwitchNotificationEvent(
                                        message=message,
                                        notification_type="redeem",
                                        timestamp=timestamp
                                    )
                                )
                                print(f"Sent instruction to EDMesg: {message}")
                            except Exception as e:
                                print(f"Error sending to EDMesg: {str(e)}")
                        else:
                            self.log_text.insert(tk.END, line)
                        self.log_text.see(tk.END)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error updating log: {str(e)}")
        
        # Schedule next update if bot is still running
        if not self.should_stop:
            self.root.after(100, self.update_log)
        else:
            self.stop_bot()

    def stop_bot(self):
        """Stop the bot and restore the main view"""
        # Signal thread to stop
        self.should_stop = True
        
        # Close EDMesg provider
        try:
            if hasattr(self, 'twitch_provider'):
                self.twitch_provider.close()
        except:
            pass
            
        # Terminate the bot process
        if self.bot_process:
            try:
                self.bot_process.terminate()
            except:
                pass
            self.bot_process = None
        
        # Wait for reading thread to finish
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=1.0)
        self.reading_thread = None
        
        # Clear queue
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except:
                pass
        
        # Hide log container and show main container
        try:
            if isinstance(self.log_container, tk.Frame):
                self.log_container.pack_forget()
            if isinstance(self.main_container, ttk.Frame):
                self.main_container.pack(fill='both', expand=True)
        except tk.TclError:
            # Handle case where widgets are already destroyed
            pass

def main():
    root = tk.Tk()
    app = ConfigManager(root)
    
    # Save config on window close
    def on_closing():
        app.save_config()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 