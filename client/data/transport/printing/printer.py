import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image, ImageWin
import win32print
import win32ui
import os
import json

class ImagePrinter:
    def __init__(self, printer_name=None):
        self.printer_name = printer_name or win32print.GetDefaultPrinter()

    def print_image(self, image_path):
        """Print an image file directly"""
        try:
            # Open printer
            hprinter = win32print.OpenPrinter(self.printer_name)
            
            # Create DC for printer
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(self.printer_name)
            
            # Start print job
            hdc.StartDoc('Image Print')
            hdc.StartPage()
            
            # Load image
            image = Image.open(image_path)
            
            # Convert image to RGB if it's not
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get printer page size in pixels (assuming 300 DPI)
            PRINTER_DPI = 300
            page_width = int(8.5 * PRINTER_DPI)  # 8.5 inches in pixels
            page_height = int(11 * PRINTER_DPI)   # 11 inches in pixels
            
            # Calculate scaling while maintaining aspect ratio
            image_aspect = image.size[0] / image.size[1]
            page_aspect = page_width / page_height
            
            if image_aspect > page_aspect:
                # Image is wider relative to its height than the page
                width = page_width
                height = int(width / image_aspect)
            else:
                # Image is taller relative to its width than the page
                height = page_height
                width = int(height * image_aspect)
            
            # Resize image
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert image to bitmap and print
            dib = ImageWin.Dib(image)
            dib.draw(hdc.GetHandleOutput(), (0, 0, width, height))
            
            # End print job
            hdc.EndPage()
            hdc.EndDoc()
            
            # Clean up
            hdc.DeleteDC()
            win32print.ClosePrinter(hprinter)
            
            print(f"Image {os.path.basename(image_path)} has been sent to printer: {self.printer_name}")
            
        except Exception as e:
            print(f"Error printing: {str(e)}")

class FileHandler(FileSystemEventHandler):
    def __init__(self, printer):
        self.printer = printer
        self.processed_filenames = set()  # Track filenames instead of full paths
        self.valid_extensions = {'.png', '.jpg', '.jpeg'}
        
        # Load processed filenames from history if exists
        if os.path.exists('processed_files.json'):
            with open('processed_files.json', 'r') as f:
                self.processed_filenames = set(json.load(f))

    def save_processed_files(self):
        """Save processed filenames to JSON"""
        with open('processed_files.json', 'w') as f:
            json.dump(list(self.processed_filenames), f)

    def on_created(self, event):
        if not event.is_directory:
            filepath = event.src_path
            filename = os.path.basename(filepath)
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Check if file is an image and filename wasn't already processed
            if file_extension in self.valid_extensions and filename not in self.processed_filenames:
                print(f"New image detected: {filename}")
                
                # Wait a moment to ensure file is completely written
                time.sleep(1)
                
                # Print image
                self.printer.print_image(filepath)
                
                # Mark filename as processed
                self.processed_filenames.add(filename)
                self.save_processed_files()

def list_printers():
    """List all available printers on the system"""
    return [printer[2] for printer in win32print.EnumPrinters(2)]

def main():
    # List available printers
    print("Available printers:")
    printers = list_printers()
    for i, printer in enumerate(printers, 1):
        print(f"{i}. {printer}")
    
    # Get user input for printer selection
    choice = '3'
    selected_printer = None
    if choice.isdigit() and 1 <= int(choice) <= len(printers):
        selected_printer = printers[int(choice)-1]
    
    # Get folder to monitor
    folder_to_watch = '.'
    if not os.path.exists(folder_to_watch):
        print("Creating folder...")
        os.makedirs(folder_to_watch)
    
    # Initialize printer and event handler
    printer = ImagePrinter(selected_printer)
    event_handler = FileHandler(printer)
    
    # Set up observer
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)
    observer.start()
    
    print(f"\nMonitoring folder: {folder_to_watch}")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()