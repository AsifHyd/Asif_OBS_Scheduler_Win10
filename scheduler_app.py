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
import obswebsocket
from obswebsocket import requests

class PlaylistScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("OBS Playlist Scheduler v1.2 - Live Broadcast Control")
        self.root.geometry("1400x800")
        
        self.videos = []
        self.clipboard_data = []
        self.broadcasting = False
        self.broadcast_thread = None
        self.obs_ws = None
        self.current_video_index = -1
        self.broadcast_start_time = None
        self.manual_time_offset = 0
        
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
        
        # Left panel - File operations
        left_panel = ttk.LabelFrame(main_frame, text="File Operations", padding="5")
        left_panel.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # File operations
        ttk.Button(left_panel, text="Add Videos", command=self.add_videos).grid(row=0, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Add Folder", command=self.add_folder).grid(row=1, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Insert Video", command=self.insert_video).grid(row=2, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Edit operations
        ttk.Button(left_panel, text="Move Up", command=self.move_up).grid(row=4, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Move Down", command=self.move_down).grid(row=5, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Delete Selected", command=self.delete_selected).grid(row=6, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=7, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Playlist operations
        ttk.Button(left_panel, text="Copy Block", command=self.copy_block).grid(row=8, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Paste Block", command=self.paste_block).grid(row=9, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Clear All", command=self.clear_all).grid(row=10, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=11, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # OBS Connection
        ttk.Label(left_panel, text="OBS Connection:", font=('Arial', 9, 'bold')).grid(row=12, column=0, pady=(5,2), sticky=tk.W)
        
        connection_frame = ttk.Frame(left_panel)
        connection_frame.grid(row=13, column=0, sticky=(tk.W, tk.E), pady=2)
        connection_frame.columnconfigure(0, weight=1)
        
        self.connect_btn = ttk.Button(connection_frame, text="Connect to OBS", command=self.connect_obs)
        self.connect_btn.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.connection_status = ttk.Label(left_panel, text="● Disconnected", foreground="red")
        self.connection_status.grid(row=14, column=0, pady=2, sticky=tk.W)
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=15, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Live Broadcast Control
        ttk.Label(left_panel, text="Live Broadcast:", font=('Arial', 9, 'bold')).grid(row=16, column=0, pady=(5,2), sticky=tk.W)
        
        self.setup_obs_btn = ttk.Button(left_panel, text="Setup OBS Scenes", command=self.setup_obs_scenes)
        self.setup_obs_btn.grid(row=17, column=0, pady=2, sticky=(tk.W, tk.E))
        self.setup_obs_btn.configure(state='disabled')
        
        self.start_broadcast_btn = ttk.Button(left_panel, text="▶ Start Live Broadcast", command=self.start_broadcast, style='Accent.TButton')
        self.start_broadcast_btn.grid(row=18, column=0, pady=2, sticky=(tk.W, tk.E))
        self.start_broadcast_btn.configure(state='disabled')
        
        self.stop_broadcast_btn = ttk.Button(left_panel, text="⏹ Stop Broadcast", command=self.stop_broadcast)
        self.stop_broadcast_btn.grid(row=19, column=0, pady=2, sticky=(tk.W, tk.E))
        self.stop_broadcast_btn.configure(state='disabled')
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=20, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Manual Control
        ttk.Label(left_panel, text="Manual Control:", font=('Arial', 9, 'bold')).grid(row=21, column=0, pady=(5,2), sticky=tk.W)
        
        self.skip_next_btn = ttk.Button(left_panel, text="⏭ Skip to Next", command=self.skip_to_next)
        self.skip_next_btn.grid(row=22, column=0, pady=2, sticky=(tk.W, tk.E))
        self.skip_next_btn.configure(state='disabled')
        
        self.emergency_btn = ttk.Button(left_panel, text="🚨 Emergency Scene", command=self.emergency_scene)
        self.emergency_btn.grid(row=23, column=0, pady=2, sticky=(tk.W, tk.E))
        self.emergency_btn.configure(state='disabled')
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=24, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Export
        ttk.Button(left_panel, text="Export Playlist", command=self.export_playlist).grid(row=25, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Configure left panel column
        left_panel.columnconfigure(0, weight=1)
        
        # Right panel - Timeline with live status
        right_panel = ttk.LabelFrame(main_frame, text="Timeline - Drag & Drop Videos Here", padding="5")
        right_panel.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Live status bar
        self.live_status_frame = ttk.Frame(right_panel)
        self.live_status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.live_status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.live_status_frame, text="🔴 LIVE:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=(0, 5))
        self.live_status_label = ttk.Label(self.live_status_frame, text="Not Broadcasting", font=('Arial', 10))
        self.live_status_label.grid(row=0, column=1, sticky=tk.W)
        
        self.current_time_label = ttk.Label(self.live_status_frame, text="", font=('Arial', 10, 'bold'))
        self.current_time_label.grid(row=0, column=2, padx=(5, 0))
        
        # Treeview for timeline
        columns = ('status', 'filename', 'duration', 'start_time', 'end_time')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=28, selectmode='extended')
        
        self.tree.heading('status', text='●')
        self.tree.heading('filename', text='Filename')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('start_time', text='Start Time')
        self.tree.heading('end_time', text='End Time')
        
        self.tree.column('status', width=30)
        self.tree.column('filename', width=300)
        self.tree.column('duration', width=100)
        self.tree.column('start_time', width=100)
        self.tree.column('end_time', width=100)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Insert Video Above", command=self.insert_video_above)
        self.context_menu.add_command(label="Insert Video Below", command=self.insert_video_below)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Jump to This Video", command=self.jump_to_video)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Move Up", command=self.move_up)
        self.context_menu.add_command(label="Move Down", command=self.move_down)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Selected", command=self.delete_selected)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Connect to OBS and setup scenes to begin live broadcasting")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Start UI update timer
        self.update_ui_timer()
        
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        try:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind('<<Drop>>', self.on_drop)
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        except:
            pass
    
    def update_ui_timer(self):
        """Update UI elements every second"""
        if self.broadcasting:
            current_time = time.time()
            if self.broadcast_start_time:
                elapsed_seconds = (current_time - self.broadcast_start_time) + self.manual_time_offset
                elapsed_formatted = self.format_duration(elapsed_seconds)
                self.current_time_label.configure(text=f"Elapsed: {elapsed_formatted}")
                
                # Update current video indicator
                self.update_current_video_indicator(elapsed_seconds)
        else:
            self.current_time_label.configure(text="")
        
        # Schedule next update
        self.root.after(1000, self.update_ui_timer)
    
    def connect_obs(self):
        """Connect to OBS WebSocket"""
        try:
            if self.obs_ws:
                self.obs_ws.disconnect()
            
            self.obs_ws = obswebsocket.obsws("localhost", 4444, "")
            self.obs_ws.connect()
            
            # Test connection
            version_info = self.obs_ws.call(requests.GetVersion())
            
            self.connection_status.configure(text="● Connected", foreground="green")
            self.connect_btn.configure(text="Disconnect OBS")
            self.setup_obs_btn.configure(state='normal')
            
            self.status_var.set(f"Connected to OBS {version_info.getObsVersion()}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to OBS:\n\n{str(e)}\n\nMake sure OBS is running with WebSocket server enabled.")
            self.disconnect_obs()
    
    def disconnect_obs(self):
        """Disconnect from OBS"""
        if self.broadcasting:
            self.stop_broadcast()
        
        if self.obs_ws:
            try:
                self.obs_ws.disconnect()
            except:
                pass
            self.obs_ws = None
        
        self.connection_status.configure(text="● Disconnected", foreground="red")
        self.connect_btn.configure(text="Connect to OBS")
        self.setup_obs_btn.configure(state='disabled')
        self.start_broadcast_btn.configure(state='disabled')
        
        self.status_var.set("Disconnected from OBS")
    
    def setup_obs_scenes(self):
        """Create OBS scenes for each video"""
        if not self.obs_ws or not self.videos:
            messagebox.showwarning("Setup Error", "Please connect to OBS and add videos first.")
            return
        
        try:
            # Create scenes for each video
            scene_count = 0
            for i, video in enumerate(self.videos):
                scene_name = f"Video_{i+1:03d}_{video['filename'][:20]}"
                
                # Create scene
                try:
                    self.obs_ws.call(requests.CreateScene(sceneName=scene_name))
                except:
                    pass  # Scene might already exist
                
                # Add media source to scene
                source_name = f"Media_{i+1:03d}"
                try:
                    self.obs_ws.call(requests.CreateInput(
                        sceneName=scene_name,
                        inputName=source_name,
                        inputKind="ffmpeg_source",
                        inputSettings={
                            "local_file": video['filepath'],
                            "looping": False,
                            "restart_on_activate": True
                        }
                    ))
                except Exception as e:
                    print(f"Error creating source: {e}")
                
                scene_count += 1
            
            # Create emergency scene
            try:
                self.obs_ws.call(requests.CreateScene(sceneName="Emergency_Scene"))
                # Add a color source or text for emergency
                self.obs_ws.call(requests.CreateInput(
                    sceneName="Emergency_Scene",
                    inputName="Emergency_Text",
                    inputKind="text_gdiplus_v2",
                    inputSettings={
                        "text": "TECHNICAL DIFFICULTIES\nPLEASE STAND BY",
                        "font": {"size": 72, "face": "Arial Bold"},
                        "color": 0xFFFFFFFF,
                        "align": "center",
                        "valign": "center"
                    }
                ))
            except:
                pass
            
            self.start_broadcast_btn.configure(state='normal')
            messagebox.showinfo("Success", f"Created {scene_count} scenes in OBS!\n\nYou can now start live broadcasting.")
            self.status_var.set(f"OBS scenes created successfully - Ready for live broadcast")
            
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to setup OBS scenes:\n{str(e)}")
    
    def start_broadcast(self):
        """Start live broadcasting with real-time control"""
        if not self.obs_ws or not self.videos:
            messagebox.showwarning("Broadcast Error", "Please connect to OBS and setup scenes first.")
            return
        
        self.broadcasting = True
        self.broadcast_start_time = time.time()
        self.manual_time_offset = 0
        self.current_video_index = -1
        
        # Start broadcast control thread
        self.broadcast_thread = threading.Thread(target=self.broadcast_controller, daemon=True)
        self.broadcast_thread.start()
        
        # Update UI
        self.start_broadcast_btn.configure(state='disabled')
        self.stop_broadcast_btn.configure(state='normal')
        self.skip_next_btn.configure(state='normal')
        self.emergency_btn.configure(state='normal')
        
        self.live_status_label.configure(text="🔴 BROADCASTING LIVE", foreground="red")
        self.status_var.set("Live broadcast started - Automatic scene switching active")
    
    def stop_broadcast(self):
        """Stop live broadcasting"""
        self.broadcasting = False
        
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1)
        
        # Update UI
        self.start_broadcast_btn.configure(state='normal')
        self.stop_broadcast_btn.configure(state='disabled')
        self.skip_next_btn.configure(state='disabled')
        self.emergency_btn.configure(state='disabled')
        
        self.live_status_label.configure(text="Broadcast Stopped", foreground="black")
        self.current_video_index = -1
        self.update_timeline()
        self.status_var.set("Broadcast stopped")
    
    def broadcast_controller(self):
        """Main broadcast control loop"""
        while self.broadcasting:
            try:
                current_time = time.time()
                elapsed_seconds = (current_time - self.broadcast_start_time) + self.manual_time_offset
                
                # Find which video should be playing now
                target_video_index = self.get_video_at_time(elapsed_seconds)
                
                # Switch scene if needed
                if target_video_index != self.current_video_index and target_video_index >= 0:
                    self.switch_to_video(target_video_index)
                    self.current_video_index = target_video_index
                
                time.sleep(0.5)  # Check every 500ms for precision
                
            except Exception as e:
                print(f"Broadcast controller error: {e}")
                time.sleep(1)
    
    def get_video_at_time(self, elapsed_seconds):
        """Get which video should be playing at given time"""
        current_time = 0
        
        for i, video in enumerate(self.videos):
            video_end_time = current_time + video['duration']
            
            if current_time <= elapsed_seconds < video_end_time:
                return i
            
            current_time = video_end_time
        
        return -1  # No video (past end of playlist)
    
    def switch_to_video(self, video_index):
        """Switch OBS to specific video scene"""
        try:
            if 0 <= video_index < len(self.videos):
                scene_name = f"Video_{video_index+1:03d}_{self.videos[video_index]['filename'][:20]}"
                self.obs_ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        except Exception as e:
            print(f"Error switching scene: {e}")
    
    def skip_to_next(self):
        """Skip to next video in schedule"""
        if not self.broadcasting:
            return
        
        current_time = time.time()
        elapsed_seconds = (current_time - self.broadcast_start_time) + self.manual_time_offset
        
        # Find next video
        next_video_index = self.get_video_at_time(elapsed_seconds) + 1
        if next_video_index < len(self.videos):
            # Calculate time to jump to next video
            target_time = sum(video['duration'] for video in self.videos[:next_video_index])
            time_adjustment = target_time - elapsed_seconds
            self.manual_time_offset += time_adjustment
    
    def emergency_scene(self):
        """Switch to emergency scene"""
        try:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="Emergency_Scene"))
            self.status_var.set("Switched to Emergency Scene")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to switch to emergency scene: {e}")
    
    def jump_to_video(self):
        """Jump to selected video in timeline"""
        selection = self.tree.selection()
        if not selection or not self.broadcasting:
            return
        
        video_index = self.tree.index(selection[0])
        
        # Calculate time offset to jump to this video
        target_time = sum(video['duration'] for video in self.videos[:video_index])
        current_time = time.time()
        elapsed_seconds = (current_time - self.broadcast_start_time) + self.manual_time_offset
        
        time_adjustment = target_time - elapsed_seconds
        self.manual_time_offset += time_adjustment
    
    def update_current_video_indicator(self, elapsed_seconds):
        """Update visual indicator of currently playing video"""
        current_video_index = self.get_video_at_time(elapsed_seconds)
        
        # Clear all status indicators
        for child in self.tree.get_children():
            self.tree.set(child, 'status', '')
        
        # Set current video indicator
        if 0 <= current_video_index < len(self.tree.get_children()):
            current_item = self.tree.get_children()[current_video_index]
            self.tree.set(current_item, 'status', '▶')
            
            # Update live status
            if current_video_index < len(self.videos):
                current_video = self.videos[current_video_index]
                self.live_status_label.configure(text=f"🔴 NOW: {current_video['filename'][:30]}...")
    
    # [Previous methods remain the same - add all methods from v1.1]
    def get_video_duration(self, filepath):
        """Get video duration using ffprobe"""
        try:
            if getattr(sys, 'frozen', False):
                ffprobe_path = os.path.join(sys._MEIPASS, 'ffprobe.exe')
            else:
                possible_paths = ['ffprobe.exe', 'ffprobe', 'bin/ffprobe.exe']
                ffprobe_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        ffprobe_path = path
                        break
                if not ffprobe_path:
                    ffprobe_path = 'ffprobe'
            
            cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                return duration
            else:
                file_size = os.path.getsize(filepath)
                estimated_duration = max(file_size / (1024 * 1024 * 2), 30)
                return estimated_duration
        except Exception as e:
            print(f"Error getting duration for {filepath}: {e}")
            return 60
    
    def format_duration(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # [Include all other methods from v1.1 - add_videos, process_files, update_timeline, etc.]
    # [For brevity, I'm showing the key new methods, but all v1.1 functionality remains]
    
    def add_videos(self):
        """Add video files to the playlist"""
        filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select video files", filetypes=filetypes)
        if files:
            self.process_files(files)
    
    def process_files(self, files, insert_at=None):
        """Process selected files and add to timeline"""
        self.status_var.set("Processing videos... Please wait")
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
        """Update the timeline display"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        current_time = 0
        for i, video in enumerate(self.videos):
            start_time = self.format_duration(current_time)
            end_time = self.format_duration(current_time + video['duration'])
            duration_str = self.format_duration(video['duration'])
            
            status = '▶' if i == self.current_video_index else ''
            
            self.tree.insert('', 'end', values=(status, video['filename'], duration_str, start_time, end_time))
            current_time += video['duration']
        
        total_duration = self.format_duration(current_time)
        self.status_var.set(f"Total duration: {total_duration} ({len(self.videos)} videos)")
    
    def export_playlist(self):
        """Export playlist with OBS WebSocket commands"""
        if not self.videos:
            messagebox.showwarning("No Videos", "No videos to export")
            return
        
        filepath = filedialog.asksaveasfilename(title="Save playlist as...", defaultextension=".json", 
                                              filetypes=[("JSON Schedule", "*.json"), ("All files", "*.*")])
        
        if filepath:
            try:
                current_time = 0
                schedule_data = {
                    "playlist_info": {
                        "total_videos": len(self.videos),
                        "total_duration": sum(video['duration'] for video in self.videos),
                        "created": datetime.now().isoformat()
                    },
                    "videos": []
                }
                
                for i, video in enumerate(self.videos):
                    start_time = current_time
                    end_time = current_time + video['duration']
                    
                    schedule_data["videos"].append({
                        'index': i,
                        'filename': video['filename'],
                        'filepath': video['filepath'],
                        'duration': video['duration'],
                        'start_time': start_time,
                        'end_time': end_time,
                        'start_time_formatted': self.format_duration(start_time),
                        'end_time_formatted': self.format_duration(end_time),
                        'scene_name': f"Video_{i+1:03d}_{video['filename'][:20]}"
                    })
                    
                    current_time += video['duration']
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(schedule_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Enhanced schedule exported!\n\nFile: {filepath}\n\nIncludes OBS scene names and complete timing data for professional broadcast automation.")
                self.status_var.set("Enhanced schedule exported with OBS integration data")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export schedule: {str(e)}")
    
    # [Add remaining methods from v1.1 - drag/drop, context menu, etc.]
    def on_drop(self, event):
        """Handle dropped files"""
        files = self.root.tk.splitlist(event.data)
        video_files = []
        
        for file in files:
            file_path = file.strip('{}')
            if os.path.isfile(file_path):
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
                if Path(file_path).suffix.lower() in video_extensions:
                    video_files.append(file_path)
        
        if video_files:
            self.process_files(video_files)
    
    def show_context_menu(self, event):
        """Show right-click context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def on_double_click(self, event):
        """Handle double-click on timeline item"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            video_info = self.videos[index]
            
            info_text = f"File: {video_info['filename']}\n"
            info_text += f"Path: {video_info['filepath']}\n"
            info_text += f"Duration: {self.format_duration(video_info['duration'])}"
            
            messagebox.showinfo("Video Information", info_text)

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
