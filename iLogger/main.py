import sys
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from gui.mainwindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    theme = "dark_teal.xml"
    apply_stylesheet(app, theme=theme)
    
    window = MainWindow()
    window.current_theme = theme  # Guarda o tema atual para alternância
    window.show()
    sys.exit(app.exec())