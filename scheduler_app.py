import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import sys
from pathlib import Path
import time
import threading
from datetime import datetime, timedelta
from tkinterdnd2 import DND_FILES, TkinterDnD
import obsws_python as obs

class PlaylistScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("OBS Playlist Scheduler v1.2 - Live Broadcast Automation")
        self.root.geometry("1400x800")
        
        self.videos = []
        self.clipboard_data = []
        self.broadcasting = False
        self.broadcast_thread = None
        self.obs_client = None
        self.current_video_index = -1
        self.broadcast_start_time = None
        self.manual_time_offset = 0
        self.schedule_start_time = "00:00:00"  # NEW: Custom start time
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left panel - Control center
        left_panel = ttk.LabelFrame(main_frame, text="Broadcast Control Center", padding="5")
        left_panel.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # File operations
        ttk.Label(left_panel, text="📁 File Management", font=('Arial', 9, 'bold')).grid(row=0, column=0, pady=(0,5), sticky=tk.W)
        ttk.Button(left_panel, text="Add Videos", command=self.add_videos).grid(row=1, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Add Folder", command=self.add_folder).grid(row=2, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Insert Video", command=self.insert_video).grid(row=3, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # NEW: Schedule Start Time
        ttk.Label(left_panel, text="⏰ Schedule Settings", font=('Arial', 9, 'bold')).grid(row=5, column=0, pady=(0,5), sticky=tk.W)
        
        time_frame = ttk.Frame(left_panel)
        time_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=2)
        time_frame.columnconfigure(1, weight=1)
        
        ttk.Label(time_frame, text="Start Time:").grid(row=0, column=0, padx=(0,5))
        self.start_time_var = tk.StringVar(value="00:00:00")
        self.start_time_entry = ttk.Entry(time_frame, textvariable=self.start_time_var, width=10)
        self.start_time_entry.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Button(left_panel, text="⏰ Set Current Time", command=self.set_current_time).grid(row=7, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=8, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Edit operations
        ttk.Label(left_panel, text="✏️ Playlist Editing", font=('Arial', 9, 'bold')).grid(row=9, column=0, pady=(0,5), sticky=tk.W)
        ttk.Button(left_panel, text="Move Up", command=self.move_up).grid(row=10, column=0, pady=1, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Move Down", command=self.move_down).grid(row=11, column=0, pady=1, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Delete Selected", command=self.delete_selected).grid(row=12, column=0, pady=1, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=13, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Block operations
        ttk.Label(left_panel, text="📋 Block Operations", font=('Arial', 9, 'bold')).grid(row=14, column=0, pady=(0,5), sticky=tk.W)
        ttk.Button(left_panel, text="Copy Block", command=self.copy_block).grid(row=15, column=0, pady=1, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Paste Block", command=self.paste_block).grid(row=16, column=0, pady=1, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Clear All", command=self.clear_all).grid(row=17, column=0, pady=1, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=18, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # OBS Connection
        ttk.Label(left_panel, text="🔗 OBS Connection", font=('Arial', 9, 'bold')).grid(row=19, column=0, pady=(0,5), sticky=tk.W)
        
        self.connect_btn = ttk.Button(left_panel, text="Connect to OBS", command=self.connect_obs)
        self.connect_btn.grid(row=20, column=0, pady=2, sticky=(tk.W, tk.E))
        
        self.connection_status = ttk.Label(left_panel, text="● Disconnected", foreground="red", font=('Arial', 8))
        self.connection_status.grid(row=21, column=0, sticky=tk.W)
        
        self.setup_btn = ttk.Button(left_panel, text="🎬 Setup OBS Scenes", command=self.setup_obs_scenes)
        self.setup_btn.grid(row=22, column=0, pady=2, sticky=(tk.W, tk.E))
        self.setup_btn.configure(state='disabled')
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=23, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Live broadcast controls
        ttk.Label(left_panel, text="🔴 Live Broadcast", font=('Arial', 9, 'bold')).grid(row=24, column=0, pady=(0,5), sticky=tk.W)
        
        self.start_btn = ttk.Button(left_panel, text="▶ Start Broadcasting", command=self.start_broadcast)
        self.start_btn.grid(row=25, column=0, pady=2, sticky=(tk.W, tk.E))
        self.start_btn.configure(state='disabled')
        
        self.stop_btn = ttk.Button(left_panel, text="⏹ Stop Broadcasting", command=self.stop_broadcast)
        self.stop_btn.grid(row=26, column=0, pady=2, sticky=(tk.W, tk.E))
        self.stop_btn.configure(state='disabled')
        
        # Manual controls
        self.skip_btn = ttk.Button(left_panel, text="⏭ Skip to Next", command=self.skip_to_next)
        self.skip_btn.grid(row=27, column=0, pady=1, sticky=(tk.W, tk.E))
        self.skip_btn.configure(state='disabled')
        
        self.emergency_btn = ttk.Button(left_panel, text="🚨 Emergency Scene", command=self.emergency_scene)
        self.emergency_btn.grid(row=28, column=0, pady=1, sticky=(tk.W, tk.E))
        self.emergency_btn.configure(state='disabled')
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=29, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Export
        ttk.Button(left_panel, text="💾 Export Playlist", command=self.export_playlist).grid(row=30, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Configure left panel column
        left_panel.columnconfigure(0, weight=1)
        
        # Right panel - Timeline
        right_panel = ttk.LabelFrame(main_frame, text="🎬 Timeline & Live Status", padding="5")
        right_panel.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Live status bar
        status_frame = ttk.Frame(right_panel)
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,5))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="🔴 LIVE:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=(0,5))
        self.live_status_label = ttk.Label(status_frame, text="Not Broadcasting", font=('Arial', 10))
        self.live_status_label.grid(row=0, column=1, sticky=tk.W)
        
        self.time_label = ttk.Label(status_frame, text="", font=('Arial', 10, 'bold'))
        self.time_label.grid(row=0, column=2, padx=(5,0))
        
        # Timeline tree
        columns = ('status', 'filename', 'duration', 'start_time', 'end_time')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=28, selectmode='extended')
        
        self.tree.heading('status', text='●')
        self.tree.heading('filename', text='Filename')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('start_time', text='Start Time')
        self.tree.heading('end_time', text='End Time')
        
        self.tree.column('status', width=30, minwidth=30)
        self.tree.column('filename', width=300, minwidth=200)
        self.tree.column('duration', width=80, minwidth=80)
        self.tree.column('start_time', width=80, minwidth=80)
        self.tree.column('end_time', width=80, minwidth=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Jump to This Video", command=self.jump_to_video)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Insert Above", command=self.insert_video_above)
        self.context_menu.add_command(label="Insert Below", command=self.insert_video_below)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Move Up", command=self.move_up)
        self.context_menu.add_command(label="Move Down", command=self.move_down)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Set start time and connect to OBS for live automation")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10,0))
        
        # Start UI update loop
        self.update_ui_loop()
    
    def set_current_time(self):
        """Set start time to current system time"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.start_time_var.set(current_time)
        self.update_timeline()
        self.status_var.set(f"Schedule start time set to {current_time}")
    
    def time_to_seconds(self, time_str):
        """Convert HH:MM:SS to seconds"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except:
            return 0
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        try:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind('<<Drop>>', self.on_drop)
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        except:
            pass
    
    def update_ui_loop(self):
        """Update live status every second"""
        if self.broadcasting:
            current_time = time.time()
            if self.broadcast_start_time:
                elapsed = (current_time - self.broadcast_start_time) + self.manual_time_offset
                elapsed_str = self.format_duration(elapsed)
                self.time_label.configure(text=f"Elapsed: {elapsed_str}")
                
                # Update current video indicator
                self.update_current_video_indicator(elapsed)
        else:
            self.time_label.configure(text="")
        
        self.root.after(1000, self.update_ui_loop)
    
    def connect_obs(self):
        """Connect to OBS WebSocket server"""
        try:
            if self.obs_client:
                try:
                    self.obs_client.disconnect()
                except:
                    pass
            
            # Connect to OBS WebSocket v5 (port 4444 as you set)
            self.obs_client = obs.ReqClient(host='localhost', port=4444, password='', timeout=3)
            
            # Test connection
            version_info = self.obs_client.get_version()
            
            self.connection_status.configure(text="● Connected", foreground="green")
            self.connect_btn.configure(text="Disconnect", command=self.disconnect_obs)
            self.setup_btn.configure(state='normal')
            
            self.status_var.set(f"Connected to OBS {version_info.obs_version} - Ready to setup scenes")
            
        except Exception as e:
            messagebox.showerror("Connection Failed", 
                f"Could not connect to OBS WebSocket:\n\n{str(e)}\n\n" +
                "Please verify:\n" +
                "1. OBS is running\n" +
                "2. Tools → WebSocket Server Settings → Enable WebSocket server\n" +
                "3. Port is set to 4444\n" +
                "4. Password is empty (or update code)")
            self.disconnect_obs()
    
    def disconnect_obs(self):
        """Disconnect from OBS"""
        if self.broadcasting:
            self.stop_broadcast()
        
        if self.obs_client:
            try:
                self.obs_client.disconnect()
            except:
                pass
            self.obs_client = None
        
        self.connection_status.configure(text="● Disconnected", foreground="red")
        self.connect_btn.configure(text="Connect to OBS", command=self.connect_obs)
        self.setup_btn.configure(state='disabled')
        self.start_btn.configure(state='disabled')
        
        self.status_var.set("Disconnected from OBS")
    
    def setup_obs_scenes(self):
        """FIXED: Create OBS scenes with properly configured media sources"""
        if not self.obs_client or not self.videos:
            messagebox.showwarning("Setup Error", "Connect to OBS and add videos first.")
            return
        
        try:
            scene_count = 0
            failed_sources = 0
            
            for i, video in enumerate(self.videos):
                scene_name = f"Video_{i+1:03d}_{os.path.splitext(video['filename'])[0][:15]}"
                
                # Create scene first
                try:
                    self.obs_client.create_scene(scene_name)
                    print(f"Created scene: {scene_name}")
                except Exception as e:
                    print(f"Scene {scene_name} might already exist: {e}")
                
                # FIXED: Create media source with correct method
                source_name = f"Media_{i+1:03d}"
                try:
                    # Convert path format for OBS
                    file_path = os.path.abspath(video['filepath']).replace('\\', '/')
                    
                    # Create the input (media source)
                    input_settings = {
                        'local_file': file_path,
                        'is_local_file': True,
                        'looping': False,
                        'restart_on_activate': True,
                        'clear_on_media_end': True,
                        'close_when_inactive': False,
                        'speed_percent': 100,
                        'hardware_decode': False,  # Disable hardware decode
                        'color_range': 0,
                        'linear_alpha': False
                    }
                    
                    # Create the input
                    self.obs_client.create_input(
                        scene_name=scene_name,
                        input_name=source_name,
                        input_kind='ffmpeg_source',
                        input_settings=input_settings
                    )
                    
                    print(f"✅ Created media source: {source_name} with file: {file_path}")
                    scene_count += 1
                    
                except Exception as e:
                    print(f"❌ Error creating source {source_name}: {e}")
                    failed_sources += 1
                    
                    # Try alternative method with SetInputSettings
                    try:
                        # First create empty media source
                        self.obs_client.create_input(
                            scene_name=scene_name,
                            input_name=source_name,
                            input_kind='ffmpeg_source',
                            input_settings={}
                        )
                        
                        # Then set the file path
                        self.obs_client.set_input_settings(
                            input_name=source_name,
                            input_settings={'local_file': file_path, 'is_local_file': True},
                            overlay=True
                        )
                        
                        print(f"✅ Alternative method worked for: {source_name}")
                        scene_count += 1
                        failed_sources -= 1
                        
                    except Exception as e2:
                        print(f"❌ Alternative method also failed for {source_name}: {e2}")
            
            # Create emergency scene
            try:
                self.obs_client.create_scene("Emergency_Scene")
                
                text_settings = {
                    'text': 'TECHNICAL DIFFICULTIES\n\nPLEASE STAND BY',
                    'font': {'face': 'Arial', 'size': 72, 'style': 'Bold'},
                    'color': 4294967295,  # White
                    'align': 'center',
                    'valign': 'center'
                }
                
                self.obs_client.create_input(
                    scene_name="Emergency_Scene",
                    input_name="Emergency_Text",
                    input_kind='text_gdiplus_v2',
                    input_settings=text_settings
                )
            except Exception as e:
                print(f"Emergency scene error: {e}")
            
            # Report results
            if scene_count > 0:
                self.start_btn.configure(state='normal')
                message = f"✅ Created {scene_count} OBS scenes successfully!"
                if failed_sources > 0:
                    message += f"\n⚠️ {failed_sources} sources failed - check OBS scenes panel"
                messagebox.showinfo("Setup Complete", message)
                self.status_var.set(f"OBS scenes created: {scene_count} success, {failed_sources} failed")
            else:
                messagebox.showerror("Setup Failed", "Could not create any scenes. Check OBS connection and file paths.")
                
        except Exception as e:
            messagebox.showerror("Setup Failed", f"Failed to setup OBS scenes:\n{str(e)}")
    
    def start_broadcast(self):
        """Start live broadcasting with custom start time"""
        if not self.obs_client or not self.videos:
            messagebox.showwarning("Broadcast Error", "Connect to OBS and setup scenes first.")
            return
        
        self.broadcasting = True
        self.broadcast_start_time = time.time()
        
        # Calculate offset based on custom start time
        start_seconds = self.time_to_seconds(self.start_time_var.get())
        self.manual_time_offset = start_seconds
        self.current_video_index = -1
        
        # Start broadcast control thread
        self.broadcast_thread = threading.Thread(target=self.broadcast_controller, daemon=True)
        self.broadcast_thread.start()
        
        # Update UI
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.skip_btn.configure(state='normal')
        self.emergency_btn.configure(state='normal')
        
        self.live_status_label.configure(text="🔴 BROADCASTING LIVE", foreground="red")
        self.status_var.set(f"🔴 Live broadcast started from {self.start_time_var.get()}")
    
    def stop_broadcast(self):
        """Stop live broadcasting"""
        self.broadcasting = False
        
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1)
        
        # Update UI
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.skip_btn.configure(state='disabled')
        self.emergency_btn.configure(state='disabled')
        
        self.live_status_label.configure(text="Broadcast Stopped", foreground="black")
        self.current_video_index = -1
        self.update_timeline()
        self.status_var.set("Broadcast stopped - Ready to start again")
    
    def broadcast_controller(self):
        """Main broadcast loop with custom start time support"""
        while self.broadcasting:
            try:
                current_time = time.time()
                elapsed = (current_time - self.broadcast_start_time) + self.manual_time_offset
                
                # Find which video should be playing
                target_index = self.get_video_at_time(elapsed)
                
                # Switch if needed
                if target_index != self.current_video_index and target_index >= 0:
                    self.switch_to_video(target_index)
                    self.current_video_index = target_index
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"Broadcast controller error: {e}")
                time.sleep(1)
    
    def get_video_at_time(self, elapsed_seconds):
        """Determine which video should be playing at given time"""
        current_time = 0
        
        for i, video in enumerate(self.videos):
            video_end = current_time + video['duration']
            
            if current_time <= elapsed_seconds < video_end:
                return i
            
            current_time = video_end
        
        return -1
    
    def switch_to_video(self, video_index):
        """Switch OBS to specific video scene"""
        try:
            if 0 <= video_index < len(self.videos):
                scene_name = f"Video_{video_index+1:03d}_{os.path.splitext(self.videos[video_index]['filename'])[0][:15]}"
                self.obs_client.set_current_program_scene(scene_name)
                print(f"✅ Switched to: {scene_name}")
        except Exception as e:
            print(f"❌ Error switching scene: {e}")
    
    def skip_to_next(self):
        """Skip to next video in schedule"""
        if not self.broadcasting:
            return
        
        current_time = time.time()
        elapsed = (current_time - self.broadcast_start_time) + self.manual_time_offset
        
        # Find next video
        next_index = self.get_video_at_time(elapsed) + 1
        if next_index < len(self.videos):
            # Calculate time to jump to next video
            target_time = sum(video['duration'] for video in self.videos[:next_index])
            adjustment = target_time - elapsed
            self.manual_time_offset += adjustment
    
    def emergency_scene(self):
        """Switch to emergency scene immediately"""
        try:
            self.obs_client.set_current_program_scene("Emergency_Scene")
            self.status_var.set("🚨 Switched to Emergency Scene")
        except Exception as e:
            messagebox.showerror("Error", f"Emergency scene failed: {e}")
    
    def jump_to_video(self):
        """Jump to selected video"""
        selection = self.tree.selection()
        if not selection or not self.broadcasting:
            return
        
        video_index = self.tree.index(selection[0])
        target_time = sum(video['duration'] for video in self.videos[:video_index])
        
        current_time = time.time()
        elapsed = (current_time - self.broadcast_start_time) + self.manual_time_offset
        
        adjustment = target_time - elapsed
        self.manual_time_offset += adjustment
    
    def update_current_video_indicator(self, elapsed_seconds):
        """Update visual indicator of currently playing video"""
        current_index = self.get_video_at_time(elapsed_seconds)
        
        # Clear all indicators
        for child in self.tree.get_children():
            self.tree.set(child, 'status', '')
        
        # Set current indicator
        if 0 <= current_index < len(self.tree.get_children()):
            current_item = self.tree.get_children()[current_index]
            self.tree.set(current_item, 'status', '▶')
            
            if current_index < len(self.videos):
                current_video = self.videos[current_index]
                filename = current_video['filename'][:30] + "..." if len(current_video['filename']) > 30 else current_video['filename']
                self.live_status_label.configure(text=f"🔴 NOW: {filename}")
    
    # File management methods (keeping existing functionality)
    def get_video_duration(self, filepath):
        """Get video duration using ffprobe"""
        try:
            if getattr(sys, 'frozen', False):
                ffprobe_path = os.path.join(sys._MEIPASS, 'ffprobe.exe')
            else:
                ffprobe_path = 'ffprobe'
            
            cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data['format']['duration'])
            else:
                return max(os.path.getsize(filepath) / (1024 * 1024 * 2), 30)
        except:
            return 60
    
    def format_duration(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def add_videos(self):
        filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select videos", filetypes=filetypes)
        if files: self.process_files(files)
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select video folder")
        if folder:
            extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
            files = [os.path.join(folder, f) for f in os.listdir(folder) 
                    if Path(f).suffix.lower() in extensions]
            if files:
                files.sort()
                self.process_files(files)
    
    def process_files(self, files, insert_at=None):
        self.status_var.set("Processing videos...")
        self.root.update()
        
        new_videos = []
        for filepath in files:
            filename = os.path.basename(filepath)
            duration = self.get_video_duration(filepath)
            new_videos.append({'filepath': filepath, 'filename': filename, 'duration': duration})
        
        if insert_at is not None:
            for i, video in enumerate(new_videos):
                self.videos.insert(insert_at + i, video)
        else:
            self.videos.extend(new_videos)
        
        self.update_timeline()
        self.status_var.set(f"Added {len(files)} videos")
    
    def update_timeline(self):
        """Update timeline with custom start time"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Start from custom start time
        start_seconds = self.time_to_seconds(self.start_time_var.get())
        current_time = start_seconds
        
        for i, video in enumerate(self.videos):
            start_time = self.format_duration(current_time)
            end_time = self.format_duration(current_time + video['duration'])
            duration_str = self.format_duration(video['duration'])
            
            status = '▶' if i == self.current_video_index else ''
            
            self.tree.insert('', 'end', values=(status, video['filename'], duration_str, start_time, end_time))
            current_time += video['duration']
        
        total_duration = current_time - start_seconds
        total_str = self.format_duration(total_duration)
        end_time_str = self.format_duration(current_time)
        self.status_var.set(f"Schedule: {self.start_time_var.get()} to {end_time_str} | Duration: {total_str} ({len(self.videos)} videos)")
    
    # Include all other existing methods (copy_block, paste_block, etc.)...
    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        video_files = []
        for file in files:
            path = file.strip('{}')
            if os.path.isfile(path) and Path(path).suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}:
                video_files.append(path)
        if video_files: self.process_files(video_files)
    
    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def on_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            video = self.videos[index]
            info = f"File: {video['filename']}\nPath: {video['filepath']}\nDuration: {self.format_duration(video['duration'])}"
            messagebox.showinfo("Video Info", info)
    
    def get_selected_indices(self):
        return [self.tree.index(item) for item in self.tree.selection()]
    
    def move_up(self):
        indices = self.get_selected_indices()
        if not indices or indices[0] == 0: return
        for i in indices:
            self.videos[i-1], self.videos[i] = self.videos[i], self.videos[i-1]
        self.update_timeline()
    
    def move_down(self):
        indices = self.get_selected_indices()
        if not indices or indices[-1] == len(self.videos) - 1: return
        for i in reversed(indices):
            self.videos[i+1], self.videos[i] = self.videos[i], self.videos[i+1]
        self.update_timeline()
    
    def delete_selected(self):
        indices = self.get_selected_indices()
        if not indices: return
        if messagebox.askyesno("Confirm", f"Delete {len(indices)} videos?"):
            for i in reversed(indices): del self.videos[i]
            self.update_timeline()
    
    def insert_video(self):
        selection = self.tree.selection()
        insert_at = self.tree.index(selection[0]) if selection else len(self.videos)
        filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Insert videos", filetypes=filetypes)
        if files: self.process_files(files, insert_at=insert_at)
    
    def insert_video_above(self):
        selection = self.tree.selection()
        if not selection: return self.insert_video()
        self.insert_at = self.tree.index(selection[0])
        filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Insert above", filetypes=filetypes)
        if files: self.process_files(files, insert_at=self.insert_at)
    
    def insert_video_below(self):
        selection = self.tree.selection()
        if not selection: return self.insert_video()
        insert_at = self.tree.index(selection[-1]) + 1
        filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Insert below", filetypes=filetypes)
        if files: self.process_files(files, insert_at=insert_at)
    
    def clear_all(self):
        if self.videos and messagebox.askyesno("Clear All", "Clear entire playlist?"):
            self.videos.clear()
            self.update_timeline()
    
    def copy_block(self):
        if not self.videos: return
        self.clipboard_data = self.videos.copy()
        self.status_var.set(f"Copied {len(self.clipboard_data)} videos")
    
    def paste_block(self):
        if not self.clipboard_data: return
        self.videos.extend(self.clipboard_data)
        self.update_timeline()
        self.status_var.set(f"Pasted {len(self.clipboard_data)} videos")
    
    def export_playlist(self):
        if not self.videos: return
        filepath = filedialog.asksaveasfilename(title="Export schedule", defaultextension=".json", 
                                              filetypes=[("Schedule", "*.json"), ("All", "*.*")])
        if filepath:
            start_seconds = self.time_to_seconds(self.start_time_var.get())
            schedule = {"videos": [], "start_time": self.start_time_var.get(), "total_duration": sum(v['duration'] for v in self.videos)}
            current_time = start_seconds
            for i, video in enumerate(self.videos):
                schedule["videos"].append({
                    'index': i,
                    'filename': video['filename'],
                    'filepath': video['filepath'],
                    'duration': video['duration'],
                    'start_time': current_time,
                    'start_formatted': self.format_duration(current_time),
                    'end_formatted': self.format_duration(current_time + video['duration']),
                    'scene_name': f"Video_{i+1:03d}_{os.path.splitext(video['filename'])[0][:15]}"
                })
                current_time += video['duration']
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(schedule, f, indent=2)
            
            messagebox.showinfo("Success", f"Schedule exported!\n\n{filepath}")

def main():
    try:
        root = TkinterDnD.Tk()
    except:
        root = tk.Tk()
        
    app = PlaylistScheduler(root)
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    root.mainloop()

if __name__ == "__main__":
    main()
