import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pdfplumber
from PIL import Image, ImageTk

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text, x, y):
        # Update existing tip if open
        if self.tip_window:
            # We can update the text and position
            self.label.config(text=text)
            self.tip_window.wm_geometry(f"+{x+10}+{y+10}")
            return
        
        if not text:
            return
            
        self.tip_window = tw = tk.Toplevel(self.widget)
        # Remove window decorations
        tw.wm_overrideredirect(True)
        
        # Position the tooltip
        tw.wm_geometry(f"+{x+10}+{y+10}")
        
        self.label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        self.label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class PDFAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Analyzer")
        self.root.geometry("1200x800")

        # State
        self.current_folder = r"E:\Utilisateur\Documents\Programmation\Python\Socleo-OCR\BC-Exemple"
        self.pdf_files = []
        self.open_pdfs = {}  # path -> pdfplumber.PDF object
        self.page_images = {} # path -> ImageTk.PhotoImage
        self.page_data = {}   # path -> list of words/rects with bboxes
        self.tooltips = {} # canvas -> ToolTip instance
        self.view_states = {} # path -> dict with state

        # Layout
        self.main_paned = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Left panel: Controls and File List
        self.left_panel = tk.Frame(self.main_paned, width=250, bg="#f0f0f0")
        self.main_paned.add(self.left_panel, minsize=200)

        # Right panel: Visualization Area
        self.right_panel = tk.Frame(self.main_paned, bg="white")
        self.main_paned.add(self.right_panel, minsize=600)

        # -- Left Panel Content --
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

        # -- Right Panel Content (Canvas Area) --
        self.view_container = tk.Frame(self.right_panel, bg="white")
        self.view_container.pack(fill=tk.BOTH, expand=True)

        # Initial load if folder exists
        if os.path.exists(self.current_folder):
            self.populate_file_list()

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
        for widget in self.view_container.winfo_children():
            widget.destroy()

        # Close previously open pdfs
        for path, pdf in self.open_pdfs.items():
            try:
                pdf.close()
            except:
                pass
        self.open_pdfs.clear()
        self.page_images.clear()
        self.page_data.clear()
        self.tooltips.clear()
        self.view_states.clear()

        if not filenames:
            lbl = tk.Label(self.view_container, text="Select a PDF to view", bg="white", font=("Arial", 14))
            lbl.pack(expand=True)
            return

        for i, fname in enumerate(filenames):
            path = os.path.join(self.current_folder, fname)
            
            # Container Frame for this PDF
            frame = tk.Frame(self.view_container, bg="white", bd=2, relief=tk.SUNKEN)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Header Frame
            header = tk.Frame(frame, bg="#ddd")
            header.pack(fill=tk.X)
            
            lbl_title = tk.Label(header, text=fname, font=("Arial", 10, "bold"), bg="#ddd")
            lbl_title.pack(side=tk.LEFT, padx=5)

            # Copy File Data Button
            btn_copy_file = tk.Button(header, text="Copy File Data", font=("Arial", 8),
                                      command=lambda p=path: self.copy_file_data(p))
            btn_copy_file.pack(side=tk.LEFT, padx=10)

            # Navigation Controls
            btn_prev = tk.Button(header, text="<", command=lambda p=path: self.change_page(p, -1))
            btn_prev.pack(side=tk.RIGHT, padx=2)
            
            lbl_page = tk.Label(header, text="Page 1", bg="#ddd")
            lbl_page.pack(side=tk.RIGHT, padx=5)
            
            btn_next = tk.Button(header, text=">", command=lambda p=path: self.change_page(p, 1))
            btn_next.pack(side=tk.RIGHT, padx=2)

            # Canvas for drawing with scrollbars
            canvas_frame = tk.Frame(frame)
            canvas_frame.pack(fill=tk.BOTH, expand=True)
            
            v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
            h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
            
            canvas = tk.Canvas(canvas_frame, bg="gray", 
                               yscrollcommand=v_scroll.set, 
                               xscrollcommand=h_scroll.set)
            
            v_scroll.config(command=canvas.yview)
            h_scroll.config(command=canvas.xview)
            
            v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Zoom bindings (Ctrl+MouseWheel)
            canvas.bind("<Control-MouseWheel>", lambda event, p=path: self.on_zoom(event, p))
            # Linux bindings
            canvas.bind("<Control-Button-4>", lambda event, p=path: self.on_zoom(event, p))
            canvas.bind("<Control-Button-5>", lambda event, p=path: self.on_zoom(event, p))

            # Hover binding (Mouse Move)
            canvas.bind("<Motion>", lambda event, p=path: self.on_mouse_move(event, p))

            # Click binding (Copy)
            canvas.bind("<Button-1>", lambda event, p=path: self.on_click(event, p))

            # Initialize tooltip for this canvas
            self.tooltips[canvas] = ToolTip(canvas)

            # Initial State
            self.view_states[path] = {
                "page": 0,
                "canvas": canvas,
                "lbl_page": lbl_page,
                "zoom": 1.0,           # View zoom level (multiplier of base_scale image)
                "base_scale": 3.0,     # The high-res render scale
                "original_img": None,  # The high-res PIL image
                "frame": frame         # Reference to container to calculate fit width
            }

            # Update commands
            btn_prev.config(command=lambda p=path: self.change_page(p, -1))
            btn_next.config(command=lambda p=path: self.change_page(p, 1))

            # Load and render
            # Use 'after' to ensure frame has geometry for auto-fit logic
            self.root.after(100, lambda p=path, c=canvas: self.load_pdf_page(p, c, page_num=0, auto_fit=True))

    def change_page(self, path, delta):
        if path not in self.view_states:
            return
        
        state = self.view_states[path]
        pdf = self.open_pdfs.get(path)
        if not pdf:
            return

        new_page = state["page"] + delta
        if 0 <= new_page < len(pdf.pages):
            state["page"] = new_page
            state["lbl_page"].config(text=f"Page {new_page + 1}")
            self.load_pdf_page(path, state["canvas"], new_page, auto_fit=False) # Keep zoom on page change?

    def load_pdf_page(self, path, canvas, page_num=0, auto_fit=False):
        try:
            if path in self.open_pdfs:
                pdf = self.open_pdfs[path]
            else:
                pdf = pdfplumber.open(path)
                self.open_pdfs[path] = pdf
            
            if page_num >= len(pdf.pages):
                return

            page = pdf.pages[page_num]
            state = self.view_states[path]
            
            # High-res rendering (Base)
            base_scale = state["base_scale"]
            im_obj = page.to_image(resolution=72 * base_scale)
            pil_image = im_obj.original
            state["original_img"] = pil_image

            # Extract words for bounding boxes
            words = page.extract_words()
            self.page_data[path] = words

            # Auto fit logic
            if auto_fit:
                frame_width = state["frame"].winfo_width()
                # Subtract scrollbar approx width and padding
                available_width = frame_width - 30 
                if available_width > 100:
                    img_w = pil_image.width
                    # Calculate zoom needed to fit width
                    # current img is at base_scale. 
                    # We want displayed width = available_width
                    # displayed_width = img_w * zoom
                    # zoom = available_width / img_w
                    new_zoom = available_width / img_w
                    state["zoom"] = new_zoom
                else:
                    # Fallback if frame not ready or too small, zoom out a bit to be safe
                    state["zoom"] = 0.3 # Rough guess for 1080p screen vs 3.0 scale

            self.display_current_page(path)
            
        except Exception as e:
            print(f"Error loading {path}: {e}")
            tk.Label(canvas, text=f"Error: {e}", fg="red").pack()

    def on_zoom(self, event, path):
        if path not in self.view_states:
            return
        
        state = self.view_states[path]
        
        # Respond to Windows (event.delta) or Linux (num)
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1

        state["zoom"] *= factor
        self.display_current_page(path)

    def on_mouse_move(self, event, path):
        if path not in self.view_states:
            return
            
        state = self.view_states[path]
        canvas = state["canvas"]
        
        # Get mouse position in canvas coordinates (accounting for scroll)
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)
        
        # Current scale factors
        current_zoom = state["zoom"]
        base_scale = state["base_scale"]
        total_scale = base_scale * current_zoom

        # Initialize found_word before loop
        found_word = None

        # --- Update Crosshair Cursor ---
        # Calculate PDF coordinates (un-scale)
        pdf_x = canvas_x / total_scale
        pdf_y = canvas_y / total_scale
        
        self.draw_crosshair(canvas, canvas_x, canvas_y, pdf_x, pdf_y, found_word)
        # -------------------------------

        # Find word under cursor
        words = self.page_data.get(path, [])
        found_word = None
        
        for word in words:
            # Scale word bbox to current view
            wx0 = word['x0'] * total_scale
            wtop = word['top'] * total_scale
            wx1 = word['x1'] * total_scale
            wbottom = word['bottom'] * total_scale
            
            if wx0 <= canvas_x <= wx1 and wtop <= canvas_y <= wbottom:
                found_word = word
                break
        
        # Update state with found word (for copy functionality)
        state["hovered_word"] = found_word
        
        if found_word:
            text_content = (f"Text: {found_word['text']}\n"
                            f"x0: {found_word['x0']:.2f}, top: {found_word['top']:.2f}\n"
                            f"x1: {found_word['x1']:.2f}, bottom: {found_word['bottom']:.2f}")
            self.show_hover_data(canvas, event, text_content)
        else:
            self.hide_hover_data(canvas)
            
        # Draw crosshair LAST so it's on top
        # Calculate PDF coordinates (un-scale)
        pdf_x = canvas_x / total_scale
        pdf_y = canvas_y / total_scale
        
        self.draw_crosshair(canvas, canvas_x, canvas_y, pdf_x, pdf_y, found_word)

    def on_click(self, event, path):
        if path not in self.view_states:
            return
        state = self.view_states[path]
        
        # If we are hovering a word, copy it
        if state.get("hovered_word"):
            self.copy_to_clipboard(state["hovered_word"])

    def draw_crosshair(self, canvas, x, y, pdf_x, pdf_y, found_word):
        # Remove old crosshair
        canvas.delete("crosshair")
        
        # Get canvas current view boundaries
        region = canvas.bbox("all")
        if not region:
            return
        min_x, min_y, max_x, max_y = region

        # Draw vertical line
        canvas.create_line(x, min_y, x, max_y, fill="blue", dash=(4, 4), tags="crosshair")
        # Draw horizontal line
        canvas.create_line(min_x, y, max_x, y, fill="blue", dash=(4, 4), tags="crosshair")

        # Fixed top-left UI
        view_x = canvas.canvasx(0)
        view_y = canvas.canvasy(0)
        
        coord_text = f"X: {pdf_x:.2f}, Y: {pdf_y:.2f}"
        
        # Box width
        box_width = 120
        
        # Draw background
        canvas.create_rectangle(view_x + 5, view_y + 5, view_x + box_width, view_y + 25, 
                                fill="white", outline="black", tags="crosshair")
        
        # Draw Coords
        canvas.create_text(view_x + 10, view_y + 15, text=coord_text, anchor="w", fill="black", tags="crosshair")

    def copy_to_clipboard(self, word_data):
        try:
            # Format data nicely
            data_str = str(word_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(data_str)
            self.root.update() # Required to finalize clipboard
            
            # Show temporary overlay message instead of blocking alert
            self.show_toast("Word Copied!")
            
        except Exception as e:
            print(f"Copy failed: {e}")

    def show_toast(self, message, duration=1000):
        # Create a transient window
        toast = tk.Toplevel(self.root)
        toast.wm_overrideredirect(True)
        
        # Position it centered or near mouse? Let's center on screen for visibility
        x = self.root.winfo_x() + self.root.winfo_width() // 2
        y = self.root.winfo_y() + self.root.winfo_height() // 2
        toast.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(toast, text=message, bg="black", fg="white", padx=20, pady=10, font=("Arial", 12))
        label.pack()
        
        # Auto destroy
        toast.after(duration, toast.destroy)

    def copy_file_data(self, path):
        try:
            # Extract data from ALL pages
            all_data = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    words = page.extract_words()
                    # Add page number to each word for context
                    for w in words:
                        w['page'] = i + 1
                    all_data.extend(words)
            
            data_str = str(all_data)
            self.root.clipboard_clear()
            self.root.clipboard_append(data_str)
            self.root.update()
            
            messagebox.showinfo("Copied", f"Extracted data from {len(all_data)} words across all pages to clipboard.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy file data: {e}")

    def display_current_page(self, path):
        if path not in self.view_states:
            return
        
        state = self.view_states[path]
        canvas = state["canvas"]
        pil_image = state["original_img"]
        
        if not pil_image:
            return

        # Resize for display
        current_zoom = state["zoom"]
        new_w = int(pil_image.width * current_zoom)
        new_h = int(pil_image.height * current_zoom)
        
        # Use simple resizing for speed during zoom
        resized_pil = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_pil)
        
        # Keep reference!
        self.page_images[path] = tk_img 
        
        # Update Canvas
        canvas.delete("all") # Clear everything including bboxes
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.config(scrollregion=(0, 0, new_w, new_h))

        # Re-draw bboxes
        # Original words are in PDF points (1/72 inch)
        # We rendered at resolution = 72 * base_scale
        # So original_img pixels = PDF_points * base_scale
        # We displayed at original_img * zoom
        # So effective scale factor from PDF points to Screen Pixels is:
        # scale = base_scale * zoom
        
        total_scale = state["base_scale"] * current_zoom
        words = self.page_data.get(path, [])
        self.draw_bboxes(canvas, words, scale=total_scale)

    def draw_bboxes(self, canvas, words, scale):
        # We don't delete 'bbox' here anymore because display_current_page deletes 'all'
        # And we don't need tag binds anymore since we use <Motion> on canvas
        
        for i, word in enumerate(words):
            x0 = word['x0'] * scale
            top = word['top'] * scale
            x1 = word['x1'] * scale
            bottom = word['bottom'] * scale
            
            canvas.create_rectangle(x0, top, x1, bottom, 
                                    outline="red", width=1, 
                                    tags="bbox")

    def show_hover_data(self, canvas, event, text):
        if canvas in self.tooltips:
            # Show tooltip near mouse cursor
            self.tooltips[canvas].show_tip(text, event.x_root, event.y_root)

    def hide_hover_data(self, canvas):
        if canvas in self.tooltips:
            self.tooltips[canvas].hide_tip()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFAnalyzerApp(root)
    root.mainloop()
