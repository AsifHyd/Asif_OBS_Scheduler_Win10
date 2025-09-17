import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
from tkinterdnd2 import DND_FILES, TkinterDnD

class PlaylistScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("OBS Playlist Scheduler v1.1")
        self.root.geometry("1200x700")
        
        self.videos = []
        self.clipboard_data = []
        
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
        
        ttk.Button(left_panel, text="Add Videos", command=self.add_videos).grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Add Folder", command=self.add_folder).grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Insert Video", command=self.insert_video).grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(left_panel, text="Move Up", command=self.move_up).grid(row=4, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Move Down", command=self.move_down).grid(row=5, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=6, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(left_panel, text="Delete Selected", command=self.delete_selected).grid(row=7, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Clear All", command=self.clear_all).grid(row=8, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=9, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(left_panel, text="Copy Block", command=self.copy_block).grid(row=10, column=0, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(left_panel, text="Paste Block", command=self.paste_block).grid(row=11, column=0, pady=2, sticky=(tk.W, tk.E))
        
        ttk.Separator(left_panel, orient='horizontal').grid(row=12, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(left_panel, text="Export Playlist", command=self.export_playlist).grid(row=13, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Configure left panel column
        left_panel.columnconfigure(0, weight=1)
        
        # Right panel - Timeline
        right_panel = ttk.LabelFrame(main_frame, text="Timeline - Drag & Drop Videos Here", padding="5")
        right_panel.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for timeline
        columns = ('filename', 'duration', 'start_time', 'end_time')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=25, selectmode='extended')
        
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
        
        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Insert Video Above", command=self.insert_video_above)
        self.context_menu.add_command(label="Insert Video Below", command=self.insert_video_below)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Move Up", command=self.move_up)
        self.context_menu.add_command(label="Move Down", command=self.move_down)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Selected", command=self.delete_selected)
        
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click
        self.tree.bind("<Double-1>", self.on_double_click)    # Double-click
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Drag videos here or use Add Videos button")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        try:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind('<<Drop>>', self.on_drop)
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        except:
            # If tkinterdnd2 not available, just continue without drag-drop
            pass
    
    def on_drop(self, event):
        """Handle dropped files"""
        files = self.root.tk.splitlist(event.data)
        video_files = []
        
        for file in files:
            file_path = file.strip('{}')  # Remove braces if present
            if os.path.isfile(file_path):
                # Check if it's a video file
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
                if Path(file_path).suffix.lower() in video_extensions:
                    video_files.append(file_path)
            elif os.path.isdir(file_path):
                # If it's a folder, add all videos from it
                for file in os.listdir(file_path):
                    full_path = os.path.join(file_path, file)
                    if Path(full_path).suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}:
                        video_files.append(full_path)
        
        if video_files:
            self.process_files(video_files)
        else:
            messagebox.showinfo("No Videos", "No video files found in the dropped items.")
    
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
            
            # Show video info dialog
            info_text = f"File: {video_info['filename']}\n"
            info_text += f"Path: {video_info['filepath']}\n"
            info_text += f"Duration: {self.format_duration(video_info['duration'])}"
            
            messagebox.showinfo("Video Information", info_text)
    
    def get_video_duration(self, filepath):
        """Get video duration using ffprobe"""
        try:
            # Try to find ffprobe in the bundled directory
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                ffprobe_path = os.path.join(sys._MEIPASS, 'ffprobe.exe')
            else:
                # Running as script - try different locations
                possible_paths = ['ffprobe.exe', 'ffprobe', 'bin/ffprobe.exe']
                ffprobe_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        ffprobe_path = path
                        break
                if not ffprobe_path:
                    ffprobe_path = 'ffprobe'  # Hope it's in PATH
            
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
                estimated_duration = max(file_size / (1024 * 1024 * 2), 30)  # Rough estimate, min 30s
                return estimated_duration
        except Exception as e:
            print(f"Error getting duration for {filepath}: {e}")
            return 60  # Default to 1 minute if we can't determine duration
    
    def format_duration(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_selected_indices(self):
        """Get indices of selected items"""
        selection = self.tree.selection()
        if not selection:
            return []
        
        indices = []
        for item in selection:
            index = self.tree.index(item)
            indices.append(index)
        
        return sorted(indices)
    
    def add_videos(self):
        """Add video files to the playlist"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp"),
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
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
            files = []
            
            for file in os.listdir(folder):
                if Path(file).suffix.lower() in video_extensions:
                    files.append(os.path.join(folder, file))
            
            if files:
                files.sort()  # Sort alphabetically
                self.process_files(files)
            else:
                messagebox.showinfo("No Videos", "No video files found in the selected folder.")
    
    def insert_video(self):
        """Insert video at selected position"""
        selection = self.tree.selection()
        insert_index = len(self.videos)  # Default to end
        
        if selection:
            insert_index = self.tree.index(selection[0])
        
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select video files to insert",
            filetypes=filetypes
        )
        
        if files:
            self.process_files(files, insert_at=insert_index)
    
    def insert_video_above(self):
        """Insert video above selected item"""
        selection = self.tree.selection()
        if not selection:
            self.insert_video()
            return
            
        insert_index = self.tree.index(selection[0])
        
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select video files to insert above",
            filetypes=filetypes
        )
        
        if files:
            self.process_files(files, insert_at=insert_index)
    
    def insert_video_below(self):
        """Insert video below selected item"""
        selection = self.tree.selection()
        if not selection:
            self.insert_video()
            return
            
        insert_index = self.tree.index(selection[-1]) + 1  # Insert after last selected
        
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select video files to insert below",
            filetypes=filetypes
        )
        
        if files:
            self.process_files(files, insert_at=insert_index)
    
    def move_up(self):
        """Move selected videos up"""
        indices = self.get_selected_indices()
        if not indices or indices[0] == 0:  # Can't move up if first item is selected
            return
        
        # Move each selected video up by one position
        for i in indices:
            self.videos[i-1], self.videos[i] = self.videos[i], self.videos[i-1]
        
        self.update_timeline()
        
        # Reselect moved items
        for i in indices:
            item_id = self.tree.get_children()[i-1]
            self.tree.selection_add(item_id)
    
    def move_down(self):
        """Move selected videos down"""
        indices = self.get_selected_indices()
        if not indices or indices[-1] == len(self.videos) - 1:  # Can't move down if last item is selected
            return
        
        # Move each selected video down by one position (reverse order to avoid conflicts)
        for i in reversed(indices):
            self.videos[i+1], self.videos[i] = self.videos[i], self.videos[i+1]
        
        self.update_timeline()
        
        # Reselect moved items
        for i in indices:
            item_id = self.tree.get_children()[i+1]
            self.tree.selection_add(item_id)
    
    def delete_selected(self):
        """Delete selected videos"""
        indices = self.get_selected_indices()
        if not indices:
            messagebox.showwarning("No Selection", "Please select videos to delete.")
            return
        
        # Confirm deletion
        if len(indices) == 1:
            message = f"Delete '{self.videos[indices[0]]['filename']}'?"
        else:
            message = f"Delete {len(indices)} selected videos?"
        
        if messagebox.askyesno("Confirm Delete", message):
            # Remove videos in reverse order to maintain indices
            for index in reversed(indices):
                del self.videos[index]
            
            self.update_timeline()
            self.status_var.set(f"Deleted {len(indices)} video(s)")
    
    def process_files(self, files, insert_at=None):
        """Process selected files and add to timeline"""
        self.status_var.set("Processing videos... Please wait")
        self.root.update()
        
        new_videos = []
        for filepath in files:
            filename = os.path.basename(filepath)
            duration = self.get_video_duration(filepath)
            
            new_videos.append({
                'filepath': filepath,
                'filename': filename,
                'duration': duration
            })
        
        # Insert at specified position or append to end
        if insert_at is not None:
            for i, video in enumerate(new_videos):
                self.videos.insert(insert_at + i, video)
        else:
            self.videos.extend(new_videos)
        
        self.update_timeline()
        self.status_var.set(f"Added {len(files)} videos")
    
    def update_timeline(self):
        """Update the timeline display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add videos with calculated times
        current_time = 0
        
        for i, video in enumerate(self.videos):
            start_time = self.format_duration(current_time)
            end_time = self.format_duration(current_time + video['duration'])
            duration_str = self.format_duration(video['duration'])
            
            item = self.tree.insert('', 'end', values=(
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
        if self.videos and messagebox.askyesno("Confirm Clear", "Clear all videos from the playlist?"):
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
        """Export playlist to M3U and JSON formats with proper path formatting"""
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
                # Export M3U playlist with proper Windows path formatting
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("#EXTM3U\n")
                    
                    for video in self.videos:
                        duration_seconds = int(video['duration'])
                        
                        # Fix Windows path formatting for M3U compatibility
                        video_path = video['filepath']
                        
                        # Normalize backslashes to forward slashes
                        video_path = video_path.replace('\\', '/')
                        
                        # URL encode spaces for M3U compatibility
                        video_path = video_path.replace(' ', '%20')
                        
                        # Add file protocol for Windows paths
                        if not video_path.startswith('file:///'):
                            video_path = f"file:///{video_path}"
                        
                        # Write M3U entries
                        f.write(f"#EXTINF:{duration_seconds},{video['filename']}\n")
                        f.write(f"{video_path}\n")
                
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
                    f"Total duration: {self.format_duration(current_time)}\n\n"
                    f"The M3U file is now VLC compatible with proper path formatting!")
                
                self.status_var.set("Playlist exported successfully with VLC-compatible formatting")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")

def main():
    try:
        root = TkinterDnD.Tk()  # Use TkinterDnD root for drag-drop support
    except:
        root = tk.Tk()  # Fallback to regular Tk if TkinterDnD not available
        
    app = PlaylistScheduler(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
