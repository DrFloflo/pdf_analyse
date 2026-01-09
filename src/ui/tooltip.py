import tkinter as tk

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
