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
        self.root.title("OBS Playlist Scheduler v1.2 - Live Broadcast Control")
        self.root.geometry("1400x800")
        
        self.videos = []
        self.clipboard_data = []
        self.broadcasting = False
        self.broadcast_thread = None
        self.obs_client = None
        self.current_video_index = -1
        self.broadcast_start_time = None
        self.manual_time_offset = 0
        
        self.setup_ui()
        self.setup_drag_drop()
    
    # [Keep all the UI setup code the same]
    
    def connect_obs(self):
        """Connect to OBS WebSocket v5"""
        try:
            if self.obs_client:
                try:
                    self.obs_client.disconnect()
                except:
                    pass
            
            # Connect to OBS WebSocket v5 (default port 4455, but you changed to 4444)
            self.obs_client = obs.ReqClient(host='localhost', port=4444, password='', timeout=3)
            
            # Test connection
            version_info = self.obs_client.get_version()
            
            self.connection_status.configure(text="● Connected", foreground="green")
            self.connect_btn.configure(text="Disconnect OBS", command=self.disconnect_obs)
            self.setup_obs_btn.configure(state='normal')
            
            self.status_var.set(f"Connected to OBS {version_info.obs_version}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to OBS:\n\n{str(e)}\n\nMake sure:\n1. OBS is running\n2. WebSocket Server is enabled in Tools → WebSocket Server Settings\n3. Port is set to 4444\n4. No password is set (or update code with your password)")
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
        self.setup_obs_btn.configure(state='disabled')
        self.start_broadcast_btn.configure(state='disabled')
        
        self.status_var.set("Disconnected from OBS")
    
    def setup_obs_scenes(self):
        """Create OBS scenes for each video using v5 API"""
        if not self.obs_client or not self.videos:
            messagebox.showwarning("Setup Error", "Please connect to OBS and add videos first.")
            return
        
        try:
            scene_count = 0
            for i, video in enumerate(self.videos):
                scene_name = f"Video_{i+1:03d}_{video['filename'][:20]}"
                
                # Create scene
                try:
                    self.obs_client.create_scene(scene_name)
                except:
                    pass  # Scene might already exist
                
                # Add media source to scene
                source_name = f"Media_{i+1:03d}"
                try:
                    input_settings = {
                        'local_file': video['filepath'],
                        'looping': False,
                        'restart_on_activate': True,
                        'clear_on_media_end': False
                    }
                    
                    self.obs_client.create_input(
                        scene_name=scene_name,
                        input_name=source_name,
                        input_kind='ffmpeg_source',
                        input_settings=input_settings
                    )
                except Exception as e:
                    print(f"Error creating source: {e}")
                
                scene_count += 1
            
            # Create emergency scene
            try:
                self.obs_client.create_scene("Emergency_Scene")
                
                text_settings = {
                    'text': 'TECHNICAL DIFFICULTIES\nPLEASE STAND BY',
                    'font': {
                        'face': 'Arial',
                        'size': 72,
                        'style': 'Bold'
                    },
                    'color': 4294967295,  # White color
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
                print(f"Error creating emergency scene: {e}")
            
            self.start_broadcast_btn.configure(state='normal')
            messagebox.showinfo("Success", f"Created {scene_count} scenes in OBS!\n\nYou can now start live broadcasting.")
            self.status_var.set(f"OBS scenes created successfully - Ready for live broadcast")
            
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to setup OBS scenes:\n{str(e)}")
    
    def switch_to_video(self, video_index):
        """Switch OBS to specific video scene using v5 API"""
        try:
            if 0 <= video_index < len(self.videos):
                scene_name = f"Video_{video_index+1:03d}_{self.videos[video_index]['filename'][:20]}"
                self.obs_client.set_current_program_scene(scene_name)
        except Exception as e:
            print(f"Error switching scene: {e}")
    
    def emergency_scene(self):
        """Switch to emergency scene using v5 API"""
        try:
            self.obs_client.set_current_program_scene("Emergency_Scene")
            self.status_var.set("Switched to Emergency Scene")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to switch to emergency scene: {e}")
    
    # [Keep all other methods the same - UI, timeline management, etc.]
