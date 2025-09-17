import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta

class PlaylistScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("OBS Playlist Scheduler v1.0")
        self.root.geometry("1200x700")
        
        self.videos = []
        self.clipboard_data = []
        
        self.setup_ui()
        
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
        
        ttk.Button(left_panel, text="Add Videos", command=self.add_videos).grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Add Folder", command=self.add_folder).grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Clear All", command=self.clear_all).grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(left_panel, text="Copy Block", command=self.copy_block).grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Paste Block", command=self.paste_block).grid(row=5, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=6, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(left_panel, text="Export Playlist", command=self.export_playlist).grid(row=7, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Configure left panel column
        left_panel.columnconfigure(0, weight=1)
        
        # Right panel - Timeline
        right_panel = ttk.LabelFrame(main_frame, text="Timeline", padding="5")
        right_panel.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for timeline
        columns = ('filename', 'duration', 'start_time', 'end_time')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=25)
        
        self.tree.heading('filename', text='Filename')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('start_time', text='Start Time')
        self.tree.heading('end_time', text='End Time')
        
        self.tree.column('filename', width=300)
        self.tree.column('duration', width=100)
        self.tree.column('start_time', width=100)
        self.tree.column('end_time', width=100)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Drag videos or use Add Videos button")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def get_video_duration(self, filepath):
        """Get video duration using ffprobe"""
        try:
            # Try to find ffprobe in the bundled directory
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                ffprobe_path = os.path.join(sys._MEIPASS, 'ffprobe.exe')
            else:
                # Running as script
                ffprobe_path = 'ffprobe.exe'
            
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                filepath
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                return duration
            else:
                # Fallback: estimate based on file size (very rough)
                file_size = os.path.getsize(filepath)
                estimated_duration = file_size / (1024 * 1024 * 2)  # Rough estimate
                return max(estimated_duration, 30)  # Minimum 30 seconds
        except Exception as e:
            print(f"Error getting duration for {filepath}: {e}")
            return 60  # Default to 1 minute if we can't determine duration
    
    def format_duration(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def add_videos(self):
        """Add video files to the playlist"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select video files",
            filetypes=filetypes
        )
        
        if files:
            self.process_files(files)
    
    def add_folder(self):
        """Add all videos from a folder"""
        folder = filedialog.askdirectory(title="Select folder containing videos")
        if folder:
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
            files = []
            
            for file in os.listdir(folder):
                if Path(file).suffix.lower() in video_extensions:
                    files.append(os.path.join(folder, file))
            
            if files:
                files.sort()  # Sort alphabetically
                self.process_files(files)
            else:
                messagebox.showinfo("No Videos", "No video files found in the selected folder.")
    
    def process_files(self, files):
        """Process selected files and add to timeline"""
        self.status_var.set("Processing videos... Please wait")
        self.root.update()
        
        for filepath in files:
            filename = os.path.basename(filepath)
            duration = self.get_video_duration(filepath)
            
            self.videos.append({
                'filepath': filepath,
                'filename': filename,
                'duration': duration
            })
        
        self.update_timeline()
        self.status_var.set(f"Added {len(files)} videos")
    
    def update_timeline(self):
        """Update the timeline display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add videos with calculated times
        current_time = 0
        
        for video in self.videos:
            start_time = self.format_duration(current_time)
            end_time = self.format_duration(current_time + video['duration'])
            duration_str = self.format_duration(video['duration'])
            
            self.tree.insert('', 'end', values=(
                video['filename'],
                duration_str,
                start_time,
                end_time
            ))
            
            current_time += video['duration']
        
        # Update status with total duration
        total_duration = self.format_duration(current_time)
        self.status_var.set(f"Total duration: {total_duration} ({len(self.videos)} videos)")
    
    def clear_all(self):
        """Clear all videos from the playlist"""
        self.videos.clear()
        self.update_timeline()
        self.status_var.set("Playlist cleared")
    
    def copy_block(self):
        """Copy current playlist as a block"""
        if not self.videos:
            messagebox.showwarning("No Videos", "No videos to copy")
            return
        
        self.clipboard_data = self.videos.copy()
        self.status_var.set(f"Copied {len(self.clipboard_data)} videos to clipboard")
    
    def paste_block(self):
        """Paste the copied block"""
        if not self.clipboard_data:
            messagebox.showwarning("No Data", "No videos in clipboard")
            return
        
        self.videos.extend(self.clipboard_data)
        self.update_timeline()
        self.status_var.set(f"Pasted {len(self.clipboard_data)} videos")
    
    def export_playlist(self):
        """Export playlist to M3U and JSON formats"""
        if not self.videos:
            messagebox.showwarning("No Videos", "No videos to export")
            return
        
        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            title="Save playlist as...",
            defaultextension=".m3u",
            filetypes=[("M3U Playlist", "*.m3u"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                # Export M3U playlist
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("#EXTM3U\n")
                    
                    for video in self.videos:
                        duration_seconds = int(video['duration'])
                        f.write(f"#EXTINF:{duration_seconds},{video['filename']}\n")
                        f.write(f"{video['filepath']}\n")
                
                # Also export JSON schedule for advanced automation
                json_filepath = filepath.replace('.m3u', '_schedule.json')
                current_time = 0
                schedule_data = []
                
                for video in self.videos:
                    start_time = current_time
                    end_time = current_time + video['duration']
                    
                    schedule_data.append({
                        'filename': video['filename'],
                        'filepath': video['filepath'],
                        'duration': video['duration'],
                        'start_time': start_time,
                        'end_time': end_time,
                        'start_time_formatted': self.format_duration(start_time),
                        'end_time_formatted': self.format_duration(end_time)
                    })
                    
                    current_time += video['duration']
                
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    json.dump(schedule_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", 
                    f"Playlist exported successfully!\n\n"
                    f"M3U file: {filepath}\n"
                    f"JSON schedule: {json_filepath}\n\n"
                    f"Total videos: {len(self.videos)}\n"
                    f"Total duration: {self.format_duration(current_time)}")
                
                self.status_var.set("Playlist exported successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

def main():
    root = tk.Tk()
    app = PlaylistScheduler(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
