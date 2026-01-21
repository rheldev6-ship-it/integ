"""
Main entry point for the Integ desktop application.

Usage:
    python main.py              # Production
    python main.py --dev        # Development with debug
"""
import sys
import argparse
from PyQt6.QtWidgets import QApplication


def main():
    """Initialize and run the Qt application."""
    parser = argparse.ArgumentParser(description="Integ Game Integration Platform")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # TODO: Import and initialize MainWindow
    # from .ui.main_window import MainWindow
    # window = MainWindow(debug=args.dev)
    # window.show()
    
    # Placeholder for now
    print("🎮 Integ Frontend v0.1.0")
    print("Connected to backend: http://localhost:8000")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
