import sys, os
import mss
from PIL import Image
import pytesseract
import requests
import google.generativeai as genai

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QIcon, QAction, QShortcut, QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QPushButton, QTextEdit, 
    QLabel, QSlider, QDialog, QSystemTrayIcon, QMenu
)
from PySide6.QtWidgets import QSizeGrip
from PySide6.QtCore import QPoint

# ========= CONFIG =========
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Uncomment if tesseract is not in PATH:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ========= OCR + AI =========
def ocr_image(pil_img: Image.Image) -> str:
    return pytesseract.image_to_string(pil_img)

def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # free tier, fast
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "⚠️ No response from Gemini."
    except Exception as e:
        return f"⚠️ Error: {e}"

# ========= UI CLASSES =========
class AnswerDialog(QDialog):
    def __init__(self, answer, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # dragging + resizing support
        self._drag_active = False
        self._drag_pos = None
        self._resizing = False
        self._resize_start = None
        self._resize_geo = None
        self._hover = False   # for glowing effect

        # === Main Panel ===
        self.panel = QWidget(self)
        self.panel.setObjectName("answerPanel")

        v = QVBoxLayout(self.panel)
        v.setContentsMargins(14, 14, 14, 14)

        lbl = QLabel("Answer")
        lbl.setStyleSheet("font-weight:700; font-size:15px;")

        self.text = QTextEdit()
        self.text.setPlainText(answer)
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-size:13px;")

        btn_close = QPushButton("✖ Close")
        btn_close.setFixedHeight(28)
        btn_close.clicked.connect(self.close)

        v.addWidget(lbl)
        v.addWidget(self.text)
        v.addWidget(btn_close)

        # === Resize Grip (bottom-right inside panel) ===
        self.grip_widget = QLabel(self.panel)
        self.grip_widget.setFixedSize(16, 16)
        self.grip_widget.setCursor(Qt.SizeFDiagCursor)
        self.grip_widget.setStyleSheet("background: transparent;")

        def update_grip_pos():
            rect = self.panel.rect()
            self.grip_widget.move(rect.width()-18, rect.height()-18)
        self.panel.resizeEvent = lambda e: (update_grip_pos(), QWidget.resizeEvent(self.panel, e))

        # hook up events
        self.grip_widget.paintEvent = self.paint_grip
        self.grip_widget.enterEvent = self.handle_enter
        self.grip_widget.leaveEvent = self.handle_leave
        self.grip_widget.mousePressEvent = self.start_resize
        self.grip_widget.mouseMoveEvent = self.resize_move
        self.grip_widget.mouseReleaseEvent = self.stop_resize

        # === Root Layout ===
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.panel)

        # === Styling ===
        self.setStyleSheet("""
            #answerPanel {
                background: rgba(30,30,40,200);
                border-radius: 12px;
                color: #f3f3f3;
            }
            QPushButton {
                background: #e63946;
                border: none; color: white;
                border-radius: 6px;
            }
            QPushButton:hover { background: #c92c3c; }
        """)
        self.resize(360, 220)

    # === Resize handle drawing & logic ===
    def paint_grip(self, event):
        painter = QPainter(self.grip_widget)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._hover:
            gradient = QRadialGradient(self.grip_widget.rect().center(), 12)
            gradient.setColorAt(0, QColor(100, 180, 255, 180))
            gradient.setColorAt(1, QColor(100, 180, 255, 0))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.grip_widget.rect())

        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRect(4, 4, 8, 8)

    def handle_enter(self, event):
        self._hover = True
        self.grip_widget.update()

    def handle_leave(self, event):
        self._hover = False
        self.grip_widget.update()

    def start_resize(self, event):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            self._resize_start = event.globalPosition().toPoint()
            self._resize_geo = self.geometry()

    def resize_move(self, event):
        if self._resizing and event.buttons() & Qt.LeftButton:
            diff = event.globalPosition().toPoint() - self._resize_start
            new_w = max(240, self._resize_geo.width() + diff.x())
            new_h = max(180, self._resize_geo.height() + diff.y())
            self.resize(new_w, new_h)

    def stop_resize(self, event):
        self._resizing = False

    # === Dragging logic ===
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # disable drag when clicking on grip
            if self.childAt(event.pos()) == self.grip_widget:
                return
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        event.accept()

class ResizeHandle(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(16, 16)
        self.setCursor(Qt.SizeFDiagCursor)
        self._hover = False
        self._resizing = False
        self._resize_start = None
        self._resize_geo = None
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._hover:
            # Glow effect: semi-transparent expanding circle
            gradient = QRadialGradient(self.rect().center(), 12)
            gradient.setColorAt(0, QColor(100, 180, 255, 180))
            gradient.setColorAt(1, QColor(100, 180, 255, 0))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.rect())

        # Grey square handle
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRect(4, 4, 8, 8)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            self._resize_start = event.globalPosition().toPoint()
            self._resize_geo = self.parent.geometry()

    def mouseMoveEvent(self, event):
        if self._resizing and event.buttons() & Qt.LeftButton:
            diff = event.globalPosition().toPoint() - self._resize_start
            new_w = max(200, self._resize_geo.width() + diff.x())
            new_h = max(150, self._resize_geo.height() + diff.y())
            self.parent.resize(new_w, new_h)

    def mouseReleaseEvent(self, event):
        self._resizing = False

class Overlay(QWidget):
    def __init__(self, tray_icon):
        super().__init__()
        self.tray_icon = tray_icon
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Keep track of dragging
        self._drag_active = False
        self._drag_pos = None

        # === UI ===
        panel = QWidget(self)
        panel.setObjectName("panel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(12, 12, 12, 12)

        # Title row with quit button
        title_row = QtWidgets.QHBoxLayout()
        title = QLabel("ScreenSage")
        title.setStyleSheet("font-weight:700; font-size:16px;")

        btn_quit = QPushButton("✖")
        btn_quit.setFixedSize(24, 24)
        btn_quit.setStyleSheet("""
            QPushButton {
                background:#e63946;
                border:none;
                color:white;
                font-weight:bold;
                border-radius:6px;
            }
            QPushButton:hover {
                background:#a4161a;
            }
        """)
        btn_quit.clicked.connect(QtWidgets.QApplication.quit)

        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(btn_quit)

        self.promptBox = QTextEdit()
        self.promptBox.setPlaceholderText("Optional: add context (e.g. subject, hint)...")

        btn_capture = QPushButton("🔍 Capture & Answer")
        btn_capture.setFixedHeight(36)
        btn_capture.clicked.connect(self.capture_and_answer)

        row = QVBoxLayout()
        row.addWidget(QLabel("Opacity"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(30, 100)
        self.slider.setValue(85)
        self.slider.valueChanged.connect(self.update_opacity)
        row.addWidget(self.slider)

        # Add resize grip (manually show in bottom-right)
        grip_layout = QtWidgets.QHBoxLayout()
        grip_layout.addStretch()
        self.grip = QSizeGrip(self)
        self.grip.setStyleSheet("background: rgba(200,200,200,120); border-radius: 3px;")
        grip_layout.addWidget(self.grip)

        # Assemble layout
        v.addLayout(title_row)
        v.addWidget(self.promptBox)
        v.addWidget(btn_capture)
        v.addLayout(row)
        v.addLayout(grip_layout)

        root = QVBoxLayout(self)
        root.addWidget(panel)

        self.setStyleSheet("""
            #panel {
                background: rgba(40,40,50,180);
                border-radius: 14px;
                color: #f3f3f3;
            }
            QPushButton {
                background: #3a86ff; border: none;
                color: white; border-radius: 8px;
            }
            QPushButton:hover { background: #256dd9; }
            QTextEdit {
                background: rgba(255,255,255,0.08);
                border: none; color: #f3f3f3;
            }
            QLabel { font-size: 13px; }
        """)
        self.resize(320, 240)
        self.move(100, 100)

    # === Dragging logic ===
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        event.accept()

    def update_opacity(self, val):
        self.setWindowOpacity(val / 100.0)

    def capture_region(self, width=900, height=400):
        pos = QCursor.pos()
        x = max(0, int(pos.x() - width/2))
        y = max(0, int(pos.y() - height/2))
        with mss.mss() as sct:
            monitor = {"left": x, "top": y, "width": width, "height": height}
            img = sct.grab(monitor)
            pil_img = Image.frombytes("RGB", img.size, img.rgb)
            return pil_img

    def capture_and_answer(self):
        img = self.capture_region()
        text = ocr_image(img).strip()
        if not text:
            dlg = AnswerDialog("No text detected.", self)
            dlg.move(QCursor.pos() + QtCore.QPoint(20,20))
            dlg.show()
            return

        is_mcq = any(opt in text for opt in ["A)", "B)", "C)", "D)"])
        extra = self.promptBox.toPlainText().strip()

        if is_mcq:
            prompt = f"""You are solving a multiple-choice question. 
Text captured:\n{text}\n
Instructions: Pick the most likely correct option (A, B, C, or D) and give a brief explanation.
Answer format: "Correct option: X. Explanation: ...".
"""
        else:
            prompt = f"Captured text:\n{text}\n\nPlease answer the question briefly and clearly."

        if extra:
            prompt = extra + "\n\n" + prompt

        answer = ask_gemini(prompt)
        dlg = AnswerDialog(answer, self)
        dlg.move(QCursor.pos() + QtCore.QPoint(20,20))
        dlg.show()

# ========= MAIN APP =========
def main():
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("ScreenSage")

    # Tray icon
    tray = QSystemTrayIcon(QIcon.fromTheme("help-about"))
    menu = QMenu()
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.setToolTip("Screen Q&A Helper")
    tray.show()

    overlay = Overlay(tray)
    overlay.setWindowOpacity(0.85)
    overlay.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()