import tkinter as tk
from tkinter import filedialog, messagebox
import os

from .pdf_viewer import PDFViewerFrame

class PDFAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Analyzer")
        self.root.geometry("1200x800")
        
        # Determine initial folder (try to use the one from original script if possible, or CWD)
        # Using a default path similar to original or CWD
        self.current_folder = os.getcwd() 
        # Optionally, try to use the hardcoded path if it exists, otherwise CWD
        # specific_path = r"E:\Utilisateur\Documents\Programmation\Python\Socleo-OCR\BC-Exemple"
        # if os.path.exists(specific_path):
        #     self.current_folder = specific_path

        self.pdf_files = []
        self.viewer_frames = []

        # Layout
        self.main_paned = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Left panel: Controls and File List
        self.left_panel = tk.Frame(self.main_paned, width=250, bg="#f0f0f0")
        self.main_paned.add(self.left_panel, minsize=200)

        # Right panel: Visualization Area
        self.right_panel = tk.Frame(self.main_paned, bg="white")
        self.main_paned.add(self.right_panel, minsize=600)

        self._setup_left_panel()
        
        # Right Panel Content (Canvas Area)
        self.view_container = tk.Frame(self.right_panel, bg="white")
        self.view_container.pack(fill=tk.BOTH, expand=True)

        # Initial load if folder contains PDFs
        self.populate_file_list()

    def _setup_left_panel(self):
        self.btn_select_folder = tk.Button(self.left_panel, text="Select Folder", command=self.select_folder)
        self.btn_select_folder.pack(pady=10, padx=5, fill=tk.X)

        self.lbl_files = tk.Label(self.left_panel, text="PDF Files (Pick 1 or 2):", bg="#f0f0f0")
        self.lbl_files.pack(pady=5, padx=5, anchor="w")

        # Scrollbar for listbox
        self.scrollbar = tk.Scrollbar(self.left_panel)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(self.left_panel, selectmode=tk.MULTIPLE, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind("<<ListboxSelect>>", self.on_file_select)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.populate_file_list()

    def populate_file_list(self):
        self.listbox.delete(0, tk.END)
        self.pdf_files = []
        try:
            items = os.listdir(self.current_folder)
            self.pdf_files = [f for f in items if f.lower().endswith(".pdf")]
            self.pdf_files.sort()
            for f in self.pdf_files:
                self.listbox.insert(tk.END, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list files: {e}")

    def on_file_select(self, event):
        selection = self.listbox.curselection()
        # We only take the first 2 selected items for visualization
        selected_filenames = [self.listbox.get(i) for i in selection[:2]]
        self.render_pdfs(selected_filenames)

    def render_pdfs(self, filenames):
        # Clear previous view
        for frame in self.viewer_frames:
            frame.close() # Ensure we close PDF handles
            frame.destroy()
        self.viewer_frames.clear()

        # Also clear any other children of view_container (like placeholder label)
        for widget in self.view_container.winfo_children():
            widget.destroy()

        if not filenames:
            lbl = tk.Label(self.view_container, text="Select a PDF to view", bg="white", font=("Arial", 14))
            lbl.pack(expand=True)
            return

        for fname in filenames:
            path = os.path.join(self.current_folder, fname)
            
            # Create Viewer Frame
            viewer = PDFViewerFrame(self.view_container, path)
            viewer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.viewer_frames.append(viewer)
