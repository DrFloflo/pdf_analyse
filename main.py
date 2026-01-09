import tkinter as tk
from src.ui.app import PDFAnalyzerApp

def main():
    root = tk.Tk()
    app = PDFAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
