#!/usr/bin/env python3
import sys
import os
import pathlib
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QUrl, QObject, Qt
from PySide2.QtQuick import QQuickView

def main():
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName("QtQuick Application")
    app.setOrganizationName("YourCompany")

    # Configure debug output
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
    os.environ["QT_LOGGING_RULES"] = "qt.qml.connections=false"

    # Find QML file with robust path resolution
    qml_file = find_qml_file("mainwindow.qml")
    if not qml_file:
        print("Error: Could not locate QML file!", file=sys.stderr)
        return 1

    print(f"Loading QML from: {qml_file}")

    # Set up QQuickView
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(qml_file))

    # Verify QML loaded correctly
    if view.status() != QQuickView.Ready:
        print(f"QML Load Error: {view.errors()}", file=sys.stderr)
        return 1

    root = view.rootObject()
    if not root:
        print("Error: No root QML object created!", file=sys.stderr)
        return 1

    print("QML components loaded successfully")

    # Access QML elements using both methods for demonstration
    try:
        # Method 1: Using property aliases (recommended)
        text = root.property("textItem")
        button = root.property("buttonItem")

        # Method 2: Using findChild (alternative)
        if not text or not button:
            text = root.findChild(QObject, "mytext")
            button = root.findChild(QObject, "mybutton")

        if not text or not button:
            raise RuntimeError("Could not find QML components")

        # Connect signals
        button.clicked.connect(
            lambda: text.setProperty("text", "Button Clicked!"))
        
        print("UI elements connected successfully")

    except Exception as e:
        print(f"Error setting up UI: {str(e)}", file=sys.stderr)
        return 1

    # Show the window and execute app
    view.setFlags(Qt.Window | Qt.WindowCloseButtonHint)
    view.show()
    return app.exec_()

def find_qml_file(filename):
    """Search for QML file in common locations"""
    search_paths = [
        # Development paths (relative to script)
        pathlib.Path(__file__).parent / filename,
        pathlib.Path(__file__).parent.parent / "src" / filename,
        
        # Container paths
        pathlib.Path("/app") / filename,
        pathlib.Path.home() / "app" / filename,
        
        # Fallback paths
        pathlib.Path.cwd() / filename,
        pathlib.Path.cwd() / "src" / filename
    ]

    for path in search_paths:
        if path.exists():
            return str(path.resolve())
    return None

if __name__ == "__main__":
    sys.exit(main())
