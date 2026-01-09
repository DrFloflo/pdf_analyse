# PDF Analyzer

A Python desktop application for analyzing PDF documents with visual feedback. This tool allows you to inspect the internal structure of PDFs by visualizing the text bounding boxes and their exact coordinates.

## Features

*   **Folder Navigation**: Browse and select folders containing your PDF files.
*   **Split View**: Select up to 2 PDF files to view and compare side-by-side.
*   **High-Resolution Rendering**: Displays PDFs with high clarity using `pypdfium2`.
*   **Bounding Box Visualization**: Automatically draws red boxes around every detected word.
*   **Data Inspection**:
    *   **Hover Tooltips**: Move your mouse over any text to see its content and exact coordinates (x0, top, x1, bottom).
    *   **Crosshair & Coordinates**: A dashed crosshair tracks your mouse, displaying the precise PDF-point coordinates in the top-left corner.
*   **Copy Data**:
    *   **Single Word**: Click directly on any word box to copy its full data dictionary to the clipboard (with a subtle visual confirmation).
    *   **Full File**: Click the "Copy File Data" button in the header to copy the data for all words across all pages of the document.
*   **Zoom Controls**:
    *   **Auto-fit**: Pages automatically resize to fit the view width when opened.
    *   **Zoom In/Out**: Hold `Ctrl` + Scroll (or use mouse buttons 4/5 on Linux) to zoom.
*   **Navigation**: Simple Next/Previous page controls.

## Prerequisites

*   Python 3.7+
*   Dependencies listed in `requirements.txt`

## Installation

1.  Clone this repository or download the source code.
2.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the application:

    ```bash
    python pdf_analyzer.py
    ```

2.  **Select a Folder**:
    *   Click "Select Folder" to choose a directory.
    *   *Default Path*: The app attempts to open `E:\Utilisateur\Documents\Programmation\Python\Socleo-OCR\BC-Exemple` on startup.

3.  **View PDFs**:
    *   Click on a file in the left sidebar to open it.
    *   Select a second file (Ctrl+Click) to open it in the right-hand panel for comparison.

4.  **Inspect**:
    *   Move your mouse over the document to inspect coordinates and text data.
    *   Use `Ctrl + Scroll` to zoom in on details.
    *   Click any word to copy its details.

## Dependencies

*   [Tkinter](https://docs.python.org/3/library/tkinter.html): Standard Python GUI library.
*   [pdfplumber](https://github.com/jsvine/pdfplumber): For extracting text and coordinate data.
*   [Pillow (PIL)](https://python-pillow.org/): For image processing.
*   [pypdfium2](https://pypi.org/project/pypdfium2/): For high-performance PDF-to-image rendering.
