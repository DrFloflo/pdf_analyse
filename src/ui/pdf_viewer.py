import tkinter as tk
from tkinter import messagebox
import pdfplumber
from PIL import Image, ImageTk
import os

from .tooltip import ToolTip

class PDFViewerFrame(tk.Frame):
    def __init__(self, parent, file_path):
        super().__init__(parent, bg="white", bd=2, relief=tk.SUNKEN)
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        
        # State
        self.pdf = None
        self.page_image = None # Keep reference to avoid GC
        self.page_data = []    # List of words
        self.current_page_index = 0
        self.zoom_level = 1.0
        self.base_scale = 3.0 # High-res render scale
        self.original_img = None
        self.hovered_word = None
        
        # UI Setup
        self._setup_ui()
        
        # Initialize ToolTip
        self.tooltip = ToolTip(self.canvas)
        
        # Load PDF
        self.after(100, lambda: self.load_page(0, auto_fit=True))

    def _setup_ui(self):
        # Header Frame
        header = tk.Frame(self, bg="#ddd")
        header.pack(fill=tk.X)
        
        lbl_title = tk.Label(header, text=self.filename, font=("Arial", 10, "bold"), bg="#ddd")
        lbl_title.pack(side=tk.LEFT, padx=5)

        # Copy File Data Button
        btn_copy_file = tk.Button(header, text="Copy File Data", font=("Arial", 8),
                                  command=self.copy_file_data)
        btn_copy_file.pack(side=tk.LEFT, padx=10)

        # Navigation Controls
        btn_prev = tk.Button(header, text="<", command=lambda: self.change_page(-1))
        btn_prev.pack(side=tk.RIGHT, padx=2)
        
        self.lbl_page = tk.Label(header, text="Page 1", bg="#ddd")
        self.lbl_page.pack(side=tk.RIGHT, padx=5)
        
        btn_next = tk.Button(header, text=">", command=lambda: self.change_page(1))
        btn_next.pack(side=tk.RIGHT, padx=2)

        # Canvas for drawing with scrollbars
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        
        self.canvas = tk.Canvas(canvas_frame, bg="gray", 
                           yscrollcommand=v_scroll.set, 
                           xscrollcommand=h_scroll.set)
        
        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bindings
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)
        # Linux bindings
        self.canvas.bind("<Control-Button-4>", self.on_zoom)
        self.canvas.bind("<Control-Button-5>", self.on_zoom)

        # Mouse Wheel Scrolling
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        self.canvas.bind("<Button-4>", self.on_mouse_scroll)
        self.canvas.bind("<Button-5>", self.on_mouse_scroll)

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)

        # Keyboard Navigation
        self.canvas.bind("<Up>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Down>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind("<Left>", lambda e: self.canvas.xview_scroll(-1, "units"))
        self.canvas.bind("<Right>", lambda e: self.canvas.xview_scroll(1, "units"))
        
        # Page Navigation
        self.canvas.bind("<Prior>", lambda e: self.change_page(-1)) # Page Up
        self.canvas.bind("<Next>", lambda e: self.change_page(1))   # Page Down
        
        # Ensure canvas can take focus
        self.canvas.config(takefocus=1)

    def load_page(self, page_num=0, auto_fit=False):
        try:
            if not self.pdf:
                self.pdf = pdfplumber.open(self.file_path)
            
            if page_num < 0 or page_num >= len(self.pdf.pages):
                return

            self.current_page_index = page_num
            self.lbl_page.config(text=f"Page {page_num + 1}")
            
            page = self.pdf.pages[page_num]
            
            # High-res rendering (Base)
            im_obj = page.to_image(resolution=72 * self.base_scale)
            self.original_img = im_obj.original

            # Extract words for bounding boxes
            self.page_data = page.extract_words()

            # Auto fit logic
            if auto_fit:
                frame_width = self.winfo_width()
                # Subtract scrollbar approx width and padding
                available_width = frame_width - 30 
                if available_width > 100:
                    img_w = self.original_img.width
                    self.zoom_level = available_width / img_w
                else:
                    # Fallback if frame not ready or too small
                    self.zoom_level = 0.3 

            self.display_current_page()
            
        except Exception as e:
            print(f"Error loading {self.file_path}: {e}")
            tk.Label(self.canvas, text=f"Error: {e}", fg="red").pack()

    def change_page(self, delta):
        if not self.pdf:
            return
        new_page = self.current_page_index + delta
        if 0 <= new_page < len(self.pdf.pages):
            self.load_page(new_page, auto_fit=False)

    def display_current_page(self):
        if not self.original_img:
            return

        # Resize for display
        new_w = int(self.original_img.width * self.zoom_level)
        new_h = int(self.original_img.height * self.zoom_level)
        
        # Use simple resizing for speed during zoom
        resized_pil = self.original_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.page_image = ImageTk.PhotoImage(resized_pil)
        
        # Update Canvas
        self.canvas.delete("all") 
        self.canvas.create_image(0, 0, anchor="nw", image=self.page_image)
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))

        # Re-draw bboxes
        total_scale = self.base_scale * self.zoom_level
        self.draw_bboxes(total_scale)

    def draw_bboxes(self, scale):
        for word in self.page_data:
            x0 = word['x0'] * scale
            top = word['top'] * scale
            x1 = word['x1'] * scale
            bottom = word['bottom'] * scale
            
            self.canvas.create_rectangle(x0, top, x1, bottom, 
                                    outline="red", width=1, 
                                    tags="bbox")

    def on_zoom(self, event):
        # Respond to Windows (event.delta) or Linux (num)
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
        self.zoom_level *= factor
        self.display_current_page()

    def on_mouse_scroll(self, event):
        if event.state & 0x0004:  # Check if Ctrl is held down (0x0004 is Ctrl mask)
            # If Ctrl is held, do nothing (handled by on_zoom) or pass
            return
            
        # Standard scrolling
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_mouse_move(self, event):
        # Get mouse position in canvas coordinates (accounting for scroll)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Current scale factors
        total_scale = self.base_scale * self.zoom_level

        # Calculate PDF coordinates (un-scale)
        pdf_x = canvas_x / total_scale
        pdf_y = canvas_y / total_scale
        
        found_word = None
        for word in self.page_data:
            # Scale word bbox to current view
            wx0 = word['x0'] * total_scale
            wtop = word['top'] * total_scale
            wx1 = word['x1'] * total_scale
            wbottom = word['bottom'] * total_scale
            
            if wx0 <= canvas_x <= wx1 and wtop <= canvas_y <= wbottom:
                found_word = word
                break
        
        self.hovered_word = found_word
        
        if found_word:
            text_content = (f"Text: {found_word['text']}\n"
                            f"x0: {found_word['x0']:.2f}, top: {found_word['top']:.2f}\n"
                            f"x1: {found_word['x1']:.2f}, bottom: {found_word['bottom']:.2f}")
            self.tooltip.show_tip(text_content, event.x_root, event.y_root)
        else:
            self.tooltip.hide_tip()
            
        self.draw_crosshair(canvas_x, canvas_y, pdf_x, pdf_y)

    def draw_crosshair(self, x, y, pdf_x, pdf_y):
        self.canvas.delete("crosshair")
        
        region = self.canvas.bbox("all")
        if not region:
            return
        min_x, min_y, max_x, max_y = region

        # Draw lines
        self.canvas.create_line(x, min_y, x, max_y, fill="blue", dash=(4, 4), tags="crosshair")
        self.canvas.create_line(min_x, y, max_x, y, fill="blue", dash=(4, 4), tags="crosshair")

        # Fixed top-left UI
        view_x = self.canvas.canvasx(0)
        view_y = self.canvas.canvasy(0)
        
        coord_text = f"X: {pdf_x:.2f}, Y: {pdf_y:.2f}"
        
        # Draw background and text
        self.canvas.create_rectangle(view_x + 5, view_y + 5, view_x + 125, view_y + 25, 
                                fill="white", outline="black", tags="crosshair")
        self.canvas.create_text(view_x + 10, view_y + 15, text=coord_text, anchor="w", fill="black", tags="crosshair")

    def on_click(self, event):
        self.canvas.focus_set()
        if self.hovered_word:
            self.copy_to_clipboard(str(self.hovered_word))
            self.show_toast("Word Copied!")

    def copy_file_data(self):
        try:
            all_data = []
            # Use a fresh open to be safe or use self.pdf
            # Using self.pdf since it's open
            for i, page in enumerate(self.pdf.pages):
                words = page.extract_words()
                for w in words:
                    w['page'] = i + 1
                all_data.extend(words)
            
            data_str = str(all_data)
            self.copy_to_clipboard(data_str)
            messagebox.showinfo("Copied", f"Extracted data from {len(all_data)} words across all pages to clipboard.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy file data: {e}")

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() 

    def show_toast(self, message, duration=1000):
        toast = tk.Toplevel(self)
        toast.wm_overrideredirect(True)
        
        # Position centered
        x = self.winfo_rootx() + self.winfo_width() // 2
        y = self.winfo_rooty() + self.winfo_height() // 2
        toast.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(toast, text=message, bg="black", fg="white", padx=20, pady=10, font=("Arial", 12))
        label.pack()
        
        toast.after(duration, toast.destroy)

    def close(self):
        if self.pdf:
            self.pdf.close()
            self.pdf = None
