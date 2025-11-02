"""
UI Module - Auto Preenchedor
Modern drag-and-drop interface for document image collection and form automation.
"""

import sys
import os
from pathlib import Path
import json
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QFileDialog, QMessageBox, QLineEdit,
    QStackedWidget, QProgressBar, QCheckBox, QGridLayout, QMenu, QDateEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QTimer, QDate
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QPalette, QColor, QFont, QDrag
from PIL import Image

# Import our processing modules
import image_processor
import data_extractor
import web_automation

# Load environment variables from user's .auto_preenchedor_data folder
env_path = Path.home() / ".auto_preenchedor_data" / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Google AI API Key from environment or default
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


class ImageDropZone(QFrame):
    """
    A drag-and-drop zone for image files with preview functionality.
    """
    
    image_changed = pyqtSignal(str, object)  # Signal: (image_key, file_path)
    
    def __init__(self, label_text, image_key, parent=None, required=False):
        """
        Initialize an image drop zone.
        
        Args:
            label_text (str): Display label for this drop zone
            image_key (str): Unique identifier for this image type
            parent: Parent Qt widget
            required (bool): Whether this document is required (shows red asterisk)
        """
        super().__init__(parent)
        
        self.label_text = label_text
        self.image_key = image_key
        self.image_path = None
        self.is_dragging = False
        self.required = required
        
        self._setup_ui()
        self.setAcceptDrops(True)
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Style the frame
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 2px solid #3498db;
            }
        """)
        
        # Title label
        if self.required:
            label_html = f'{self.label_text} <span style="color: #e74c3c;">*</span>'
            self.title_label = QLabel(label_html)
        else:
            self.title_label = QLabel(self.label_text)
        title_font = QFont('Segoe UI', 10, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #333333; background-color: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Drop area
        self.drop_area = QLabel("Arraste a imagem aqui\nou clique para selecionar")
        self.drop_area.setMinimumSize(250, 280)
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px dashed #cccccc;
                border-radius: 5px;
                color: #888888;
                font-size: 11px;
            }
        """)
        self.drop_area.setWordWrap(True)
        self.drop_area.mousePressEvent = self._on_click
        layout.addWidget(self.drop_area)
        
        # Clear button (initially hidden)
        self.clear_btn = QPushButton("✕ Limpar")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_image)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)
        
        self.setLayout(layout)
        
    def _on_click(self, event):
        """Handle click to open file dialog."""
        if self.image_path and event.button() == Qt.LeftButton:
            # If image exists, start drag
            self.is_dragging = True
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar {self.label_text}",
            "",
            "Imagens (*.jpg *.jpeg *.png *.bmp *.gif);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            self._set_image(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        elif hasattr(event.source(), 'image_key'):  # Drag from another zone
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        # Check if dropping from another ImageDropZone
        source_zone = event.source()
        if isinstance(source_zone, ImageDropZone) and source_zone != self:
            # Transfer image from source to this zone
            image_to_transfer = source_zone.image_path
            if image_to_transfer:
                source_zone._clear_image()
                self._set_image(image_to_transfer)
            event.acceptProposedAction()
            return
        
        # Handle file drop from external source
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if self._is_valid_image(file_path):
                    self._set_image(file_path)
                    event.acceptProposedAction()
                else:
                    QMessageBox.critical(
                        self,
                        "Erro",
                        "Por favor, selecione um arquivo de imagem válido."
                    )
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton and self.image_path:
            self.is_dragging = True
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self.is_dragging and self.image_path:
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)
            
            # Create drag pixmap preview
            if self.drop_area.pixmap():
                drag.setPixmap(self.drop_area.pixmap().scaled(100, 100, Qt.KeepAspectRatio))
            
            drag.exec_(Qt.MoveAction)
            self.is_dragging = False
        super().mouseMoveEvent(event)
    
    def _set_image(self, file_path):
        """Set and display the image."""
        self.image_path = file_path
        
        try:
            # Load and display image
            pixmap = QPixmap(file_path)
            
            # Scale to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                250, 250,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Update drop area to show image
            self.drop_area.setPixmap(scaled_pixmap)
            self.drop_area.setText("")
            self.drop_area.setStyleSheet("""
                QLabel {
                    background-color: #e8e8e8;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                }
            """)
            
            # Show clear button
            self.clear_btn.show()
            
            # Emit signal
            self.image_changed.emit(self.image_key, file_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar imagem: {e}")
            self.image_path = None
    
    def _clear_image(self):
        """Clear the current image."""
        self.image_path = None
        
        self.drop_area.clear()
        self.drop_area.setText("Arraste a imagem aqui\nou clique para selecionar")
        self.drop_area.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px dashed #cccccc;
                border-radius: 5px;
                color: #888888;
                font-size: 11px;
            }
        """)
        
        self.clear_btn.hide()
        
        # Emit signal
        self.image_changed.emit(self.image_key, None)
    
    def _is_valid_image(self, file_path):
        """Check if file is a valid image."""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    def get_image_path(self):
        """Get the current image path."""
        return self.image_path


class AutoPreenchedorUI(QMainWindow):
    """
    Main UI window for Auto Preenchedor application.
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Auto Preenchedor")
        self.setGeometry(100, 100, 1100, 850)
        
        # Document images dictionary
        self.image_paths = {}
        
        # Extracted data dictionary
        self.extracted_data = {}
        
        # Organized file paths
        self.organized_files = {}
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the main UI with stacked pages."""
        # Central widget with stacked pages
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for multiple pages
        self.stacked_widget = QStackedWidget()
        
        # Page 1: Document Collection
        self.document_page = self._create_document_collection_page()
        self.stacked_widget.addWidget(self.document_page)
        
        # Page 2: Data Editing
        self.data_editing_page = self._create_data_editing_page()
        self.stacked_widget.addWidget(self.data_editing_page)
        
        main_layout.addWidget(self.stacked_widget)
        central_widget.setLayout(main_layout)
    
    def _create_document_collection_page(self):
        """Create the document collection page."""
        page = QWidget()
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #2c3e50;")
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_context_menu)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        # Open folder button (left side)
        self.open_folder_btn = QPushButton("📁 Abrir Pasta")
        self.open_folder_btn.setFixedSize(140, 50)
        folder_btn_font = QFont('Segoe UI', 10, QFont.Bold)
        self.open_folder_btn.setFont(folder_btn_font)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: #ecf0f1;
                border: 2px solid #4a5f7f;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4a5f7f;
                border-color: #5d7596;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
            }
        """)
        self.open_folder_btn.clicked.connect(self._open_organized_folder)
        header_layout.addWidget(self.open_folder_btn)
        
        # Add stretch to push title to center
        header_layout.addStretch()
        
        title_label = QLabel("📋 Auto Preenchedor de Formulários - Coleta de Documentos")
        title_font = QFont('Segoe UI', 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Add stretch to keep title centered
        header_layout.addStretch()
        
        # Add invisible spacer to balance the left button
        spacer = QWidget()
        spacer.setFixedSize(140, 50)
        header_layout.addWidget(spacer)
        
        header.setLayout(header_layout)
        page_layout.addWidget(header)
        
        # User Guide link bar (below header)
        guide_bar = QFrame()
        guide_bar.setFixedHeight(35)
        guide_bar.setStyleSheet("background-color: #34495e;")
        guide_bar_layout = QHBoxLayout()
        guide_bar_layout.setContentsMargins(15, 0, 15, 0)
        
        guide_bar_layout.addStretch()
        
        self.user_guide_btn = QPushButton("📖 Guia do Usuário")
        self.user_guide_btn.setFixedHeight(25)
        guide_btn_font = QFont('Segoe UI', 9)
        self.user_guide_btn.setFont(guide_btn_font)
        self.user_guide_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3498db;
                border: none;
                text-decoration: underline;
                padding: 2px 10px;
            }
            QPushButton:hover {
                color: #5dade2;
            }
            QPushButton:pressed {
                color: #2874a6;
            }
        """)
        self.user_guide_btn.setCursor(Qt.PointingHandCursor)
        self.user_guide_btn.clicked.connect(self._open_user_guide)
        guide_bar_layout.addWidget(self.user_guide_btn)
        
        guide_bar_layout.addStretch()
        
        guide_bar.setLayout(guide_bar_layout)
        page_layout.addWidget(guide_bar)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: none;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #f5f5f5;")
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(10)
        
        # Section: Document Collection
        scroll_layout.addWidget(self._create_section_header("Documentos do Beneficiário (Menor)"))
        
        # Name input field
        name_container = QWidget()
        name_container.setStyleSheet("background-color: transparent;")
        name_layout = QHBoxLayout()
        name_layout.setContentsMargins(10, 10, 10, 20)
        
        name_label = QLabel("Nome do Beneficiário:")
        name_label_font = QFont('Segoe UI', 11)
        name_label.setFont(name_label_font)
        name_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        name_label.setFixedWidth(180)
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome e sobrenome do beneficiário...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                font-size: 14px;
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: white;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QLineEdit::placeholder {
                color: #999999;
                font-size: 14px;
            }
        """)
        name_layout.addWidget(self.name_input)
        
        name_container.setLayout(name_layout)
        scroll_layout.addWidget(name_container)
        
        # First row - Beneficiary documents
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        
        self.cpf_beneficiario_zone = ImageDropZone("CPF do Beneficiário", "cpf_do_menor", required=True)
        self.cpf_beneficiario_zone.image_changed.connect(self._on_image_changed)
        row1.addWidget(self.cpf_beneficiario_zone)
        
        self.rg_beneficiario_zone = ImageDropZone("RG do Beneficiário", "rg_do_menor", required=False)
        self.rg_beneficiario_zone.image_changed.connect(self._on_image_changed)
        row1.addWidget(self.rg_beneficiario_zone)
        
        self.foto_3x4_zone = ImageDropZone("Foto 3x4", "foto_3x4", required=True)
        self.foto_3x4_zone.image_changed.connect(self._on_image_changed)
        row1.addWidget(self.foto_3x4_zone)
        
        scroll_layout.addLayout(row1)
        
        # Section: Responsible documents
        scroll_layout.addWidget(self._create_section_header("Documentos do Responsável"))
        
        # Second row - Responsible documents
        row2 = QHBoxLayout()
        row2.setSpacing(15)
        
        self.cpf_responsavel_zone = ImageDropZone("CPF do Responsável", "cpf_do_responsavel", required=True)
        self.cpf_responsavel_zone.image_changed.connect(self._on_image_changed)
        row2.addWidget(self.cpf_responsavel_zone)
        
        self.rg_responsavel_zone = ImageDropZone("RG do Responsável", "rg_do_responsavel", required=False)
        self.rg_responsavel_zone.image_changed.connect(self._on_image_changed)
        row2.addWidget(self.rg_responsavel_zone)
        
        # Add spacer to keep layout consistent
        row2.addStretch()
        
        scroll_layout.addLayout(row2)
        
        # Section: Additional documents
        scroll_layout.addWidget(self._create_section_header("Documentos Adicionais"))
        
        # Third row - Additional documents
        row3 = QHBoxLayout()
        row3.setSpacing(15)
        
        self.laudo_medico_zone = ImageDropZone("Laudo Médico", "laudo_medico", required=True)
        self.laudo_medico_zone.image_changed.connect(self._on_image_changed)
        row3.addWidget(self.laudo_medico_zone)
        
        self.comprovante_residencia_zone = ImageDropZone("Comprovante de Residência", "comprovante_residencia", required=True)
        self.comprovante_residencia_zone.image_changed.connect(self._on_image_changed)
        row3.addWidget(self.comprovante_residencia_zone)
        
        self.vem_zone = ImageDropZone("VEM (Vale Eletrônico Municipal)", "vem", required=False)
        self.vem_zone.image_changed.connect(self._on_image_changed)
        row3.addWidget(self.vem_zone)
        
        scroll_layout.addLayout(row3)
        
        # Add some spacing at the bottom
        scroll_layout.addStretch()
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        page_layout.addWidget(scroll_area)
        
        # Footer with navigation buttons
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("background-color: #ecf0f1;")
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(20, 15, 20, 15)
        
        # Summary label
        self.summary_label = QLabel("0/8 documentos carregados (VEM opcional)")
        summary_font = QFont('Segoe UI', 10)
        self.summary_label.setFont(summary_font)
        self.summary_label.setStyleSheet("color: #555555; background-color: transparent;")
        footer_layout.addWidget(self.summary_label)
        
        footer_layout.addStretch()
        
        # Next button (larger)
        self.next_btn_page1 = QPushButton("Próximo: Extração de Dados ➜")
        self.next_btn_page1.setFixedSize(340, 60)
        next_font = QFont('Segoe UI', 12, QFont.Bold)
        self.next_btn_page1.setFont(next_font)
        self.next_btn_page1.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.next_btn_page1.clicked.connect(self._go_to_next_step)
        self.next_btn_page1.setContextMenuPolicy(Qt.CustomContextMenu)
        self.next_btn_page1.customContextMenuRequested.connect(self._show_test_data_menu)
        footer_layout.addWidget(self.next_btn_page1)
        
        footer.setLayout(footer_layout)
        page_layout.addWidget(footer)
        
        page.setLayout(page_layout)
        return page
    
    def _create_data_editing_page(self):
        """Create the data editing and validation page."""
        page = QWidget()
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #2c3e50;")
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_context_menu)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        # Open folder button (left side) - same as page 1
        open_folder_btn_page2 = QPushButton("📁 Abrir Pasta")
        open_folder_btn_page2.setFixedSize(140, 50)
        folder_btn_font = QFont('Segoe UI', 10, QFont.Bold)
        open_folder_btn_page2.setFont(folder_btn_font)
        open_folder_btn_page2.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: #ecf0f1;
                border: 2px solid #4a5f7f;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4a5f7f;
                border-color: #5d7596;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
            }
        """)
        open_folder_btn_page2.clicked.connect(self._open_organized_folder)
        header_layout.addWidget(open_folder_btn_page2)
        
        # Add stretch to push title to center
        header_layout.addStretch()
        
        title_label = QLabel("✏️ Auto Preenchedor - Verificação e Edição de Dados")
        title_font = QFont('Segoe UI', 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Add stretch to keep title centered
        header_layout.addStretch()
        
        # Add invisible spacer to balance the left button
        spacer = QWidget()
        spacer.setFixedSize(140, 50)
        header_layout.addWidget(spacer)
        
        header.setLayout(header_layout)
        page_layout.addWidget(header)
        
        # Progress indicator
        progress_widget = QWidget()
        progress_widget.setStyleSheet("background-color: #ecf0f1;")
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(20, 10, 20, 10)
        
        self.progress_label = QLabel("Extraindo dados das imagens...")
        progress_label_font = QFont('Segoe UI', 10)
        self.progress_label.setFont(progress_label_font)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        progress_widget.setLayout(progress_layout)
        page_layout.addWidget(progress_widget)
        
        # Scroll area for data fields
        self.data_scroll_area = QScrollArea()
        self.data_scroll_area.setWidgetResizable(True)
        self.data_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: none;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #f5f5f5;")
        self.data_scroll_layout = QVBoxLayout()
        self.data_scroll_layout.setContentsMargins(40, 30, 40, 30)
        self.data_scroll_layout.setSpacing(15)
        
        # Data input fields will be added here dynamically
        self._create_data_input_fields()
        
        scroll_widget.setLayout(self.data_scroll_layout)
        self.data_scroll_area.setWidget(scroll_widget)
        
        # Connect scroll event to check if user has scrolled to bottom
        self.data_scroll_area.verticalScrollBar().valueChanged.connect(self._check_scroll_position)
        
        page_layout.addWidget(self.data_scroll_area)
        
        # Footer with navigation buttons
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("background-color: #ecf0f1;")
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(20, 15, 20, 15)
        
        # Back button
        back_btn = QPushButton("← Voltar")
        back_btn.setFixedSize(150, 60)
        back_font = QFont('Segoe UI', 11, QFont.Bold)
        back_btn.setFont(back_font)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        back_btn.clicked.connect(self._go_back_to_documents)
        footer_layout.addWidget(back_btn)
        
        # Nova Entrada button
        new_entry_btn = QPushButton("🔄 Nova Entrada")
        new_entry_btn.setFixedSize(180, 60)
        new_entry_font = QFont('Segoe UI', 11, QFont.Bold)
        new_entry_btn.setFont(new_entry_font)
        new_entry_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        new_entry_btn.clicked.connect(self._start_new_entry)
        footer_layout.addWidget(new_entry_btn)
        
        footer_layout.addStretch()
        
        # Next button (initially disabled until user scrolls to bottom)
        self.next_btn_page2 = QPushButton("Próximo: Preencher Formulários ➜")
        self.next_btn_page2.setFixedSize(400, 70)
        next_font = QFont('Segoe UI', 12, QFont.Bold)
        self.next_btn_page2.setFont(next_font)
        self.next_btn_page2.setEnabled(False)  # Start disabled
        self.next_btn_page2.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                text-align: center;
            }
            QPushButton:hover:enabled {
                background-color: #229954;
            }
            QPushButton:pressed:enabled {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #d5d8dc;
            }
        """)
        self.next_btn_page2.clicked.connect(self._go_to_form_filling)
        footer_layout.addWidget(self.next_btn_page2)
        
        footer.setLayout(footer_layout)
        page_layout.addWidget(footer)
        
        page.setLayout(page_layout)
        return page
    
    def _create_data_input_fields(self):
        """Create editable input fields for all extracted data."""
        # Data fields based on the extraction format
        fields_config = [
            ("nome_do_responsavel", "Nome do Responsável", "text"),
            ("nome_do_menor", "Nome do Beneficiário", "text"),
            ("nome_da_mae_do_menor", "Nome da Mãe do Beneficiário", "text"),
            ("cpf_do_responsavel", "CPF do Responsável", "cpf"),
            ("rg_do_responsavel", "RG do Responsável", "rg"),
            ("cpf_do_menor", "CPF do Beneficiário", "cpf"),
            ("rg_do_menor", "RG do Beneficiário", "rg"),
            ("data_de_nascimento_do_menor", "Data de Nascimento do Beneficiário (DD/MM/AAAA)", "date"),
            ("endereço", "Endereço (Rua e Número)", "text"),
            ("cep", "CEP", "cep"),
            ("telefone", "Telefone", "phone"),
            ("email", "E-mail", "text"),
        ]
        
        # Store field references
        self.data_fields = {}
        self.cid_checkboxes = {}
        
        for field_key, field_label, field_type in fields_config:
            field_container = self._create_input_field(field_key, field_label, field_type)
            self.data_scroll_layout.addWidget(field_container)
        
        # Add CID checkboxes section
        cid_container = self._create_cid_checkboxes()
        self.data_scroll_layout.addWidget(cid_container)
        
        # Add form selection checkboxes
        form_container = self._create_form_selection_checkboxes()
        self.data_scroll_layout.addWidget(form_container)
        
        self.data_scroll_layout.addStretch()
    
    def _create_input_field(self, key, label_text, field_type="text"):
        """Create a single labeled input field."""
        container = QWidget()
        container.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Label
        label = QLabel(label_text)
        label_font = QFont('Segoe UI', 11, QFont.Bold)
        label.setFont(label_font)
        label.setStyleSheet("color: #2c3e50; background-color: transparent; padding: 0;")
        layout.addWidget(label)
        
        # Create input field based on type
        if field_type == "date":
            # Use QDateEdit for date fields
            input_field = QDateEdit()
            input_field.setCalendarPopup(True)
            input_field.setDisplayFormat("dd/MM/yyyy")
            input_field.setDate(QDate.currentDate())
            
            # Disable mouse wheel scrolling to prevent accidental changes
            input_field.wheelEvent = lambda event: None
            
            input_field.setStyleSheet("""
                QDateEdit {
                    padding: 12px 15px;
                    font-size: 13px;
                    border: 2px solid #d5dbdb;
                    border-radius: 5px;
                    background-color: #fafafa;
                    color: #2c3e50;
                }
                QDateEdit:focus {
                    border: 2px solid #3498db;
                    background-color: white;
                }
                QDateEdit::drop-down {
                    border: none;
                    width: 30px;
                }
                QDateEdit::down-arrow {
                    image: url(none);
                    border: none;
                    width: 0px;
                }
            """)
        else:
            # Use QLineEdit for other fields
            input_field = QLineEdit()
            
            # Set placeholder and connect formatters based on field type
            if field_type == "phone":
                input_field.setPlaceholderText("(81) 9 9999-9999")
                input_field.textChanged.connect(lambda: self._format_phone_number(input_field))
            elif field_type == "cpf":
                input_field.setPlaceholderText("000.000.000-00")
                input_field.textChanged.connect(lambda: self._format_cpf(input_field))
            elif field_type == "rg":
                input_field.setPlaceholderText("0.000.000 ou 000.000.000-00")
                input_field.textChanged.connect(lambda: self._format_rg(input_field))
            elif field_type == "cep":
                input_field.setPlaceholderText("00000-000")
                input_field.textChanged.connect(lambda: self._format_cep(input_field))
            else:
                # Check if this is a name field that should be uppercase
                if key in ["nome_do_responsavel", "nome_do_menor", "nome_da_mae_do_menor"]:
                    input_field.textChanged.connect(lambda: self._format_uppercase(input_field))
                input_field.setPlaceholderText(f"Digite {label_text.lower()}...")
            
            input_field.setStyleSheet("""
                QLineEdit {
                    padding: 12px 15px;
                    font-size: 15px;
                    border: 2px solid #d5dbdb;
                    border-radius: 5px;
                    background-color: #fafafa;
                    color: #2c3e50;
                }
                QLineEdit:focus {
                    border: 2px solid #3498db;
                    background-color: white;
                }
                QLineEdit::placeholder {
                    color: #95a5a6;
                    font-size: 12px;
                }
            """)
        
        layout.addWidget(input_field)
        
        container.setLayout(layout)
        
        # Store reference
        self.data_fields[key] = input_field
        
        return container
        
    def _create_section_header(self, title):
        """Create a section header."""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 5)
        layout.setSpacing(5)
        
        label = QLabel(title)
        label_font = QFont('Segoe UI', 14, QFont.Bold)
        label.setFont(label_font)
        label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        layout.addWidget(label)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3498db; max-height: 2px;")
        layout.addWidget(separator)
        
        widget.setLayout(layout)
        return widget
    
    def _create_cid_checkboxes(self):
        """Create CID checkboxes section."""
        container = QWidget()
        container.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Label
        label = QLabel("CIDs - Selecione todos os aplicáveis")
        label_font = QFont('Segoe UI', 11, QFont.Bold)
        label.setFont(label_font)
        label.setStyleSheet("color: #2c3e50; background-color: transparent; padding: 0;")
        layout.addWidget(label)
        
        # Create grid for checkboxes
        checkbox_widget = QWidget()
        checkbox_widget.setStyleSheet("background-color: #fafafa; border: 2px solid #d5dbdb; border-radius: 5px; padding: 10px;")
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # CID-10 codes (F84.x)
        cid10_codes = [
            "10:F84.0", "10:F84.1", "10:F84.2", "10:F84.3",
            "10:F84.4", "10:F84.5", "10:F84.8", "10:F84.9"
        ]
        
        # CID-11 codes (6A02.x)
        cid11_codes = [
            "11:6A02.0", "11:6A02.1", "11:6A02.2", "11:6A02.3",
            "11:6A02.4", "11:6A02.5", "11:6A02.Y", "11:6A02.Z"
        ]
        
        # Add CID-10 checkboxes (left column)
        for i, cid_code in enumerate(cid10_codes):
            checkbox = QCheckBox(cid_code)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #2c3e50;
                    font-size: 12px;
                    spacing: 8px;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #95a5a6;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                    border-color: #2980b9;
                }
                QCheckBox::indicator:checked::after {
                    content: "✕";
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            grid_layout.addWidget(checkbox, i, 0)
            self.cid_checkboxes[cid_code] = checkbox
        
        # Add CID-11 checkboxes (right column)
        for i, cid_code in enumerate(cid11_codes):
            checkbox = QCheckBox(cid_code)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #2c3e50;
                    font-size: 12px;
                    spacing: 8px;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #95a5a6;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                    border-color: #2980b9;
                }
                QCheckBox::indicator:checked::after {
                    content: "✕";
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            grid_layout.addWidget(checkbox, i, 1)
            self.cid_checkboxes[cid_code] = checkbox
        
        checkbox_widget.setLayout(grid_layout)
        layout.addWidget(checkbox_widget)
        
        container.setLayout(layout)
        return container
    
    def _create_form_selection_checkboxes(self):
        """Create form selection checkboxes section."""
        container = QWidget()
        container.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Label
        label = QLabel("Formulários a Preencher")
        label_font = QFont('Segoe UI', 11, QFont.Bold)
        label.setFont(label_font)
        label.setStyleSheet("color: #2c3e50; background-color: transparent; padding: 0;")
        layout.addWidget(label)
        
        # Create container for checkboxes
        checkbox_widget = QWidget()
        checkbox_widget.setStyleSheet("background-color: #fafafa; border: 2px solid #d5dbdb; border-radius: 5px; padding: 10px;")
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(10)
        
        # CIPTEA Primeira Via
        self.ciptea_primeira_checkbox = QCheckBox("CIPTEA Primeira Via")
        self.ciptea_primeira_checkbox.setChecked(True)  # Default checked
        self.ciptea_primeira_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #95a5a6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
            QCheckBox::indicator:checked::after {
                content: "✕";
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.ciptea_primeira_checkbox.stateChanged.connect(self._on_primeira_via_changed)
        self.ciptea_primeira_checkbox.stateChanged.connect(self._check_form_selection)
        checkbox_layout.addWidget(self.ciptea_primeira_checkbox)
        
        # CIPTEA Segunda Via
        self.ciptea_segunda_checkbox = QCheckBox("CIPTEA Segunda Via")
        self.ciptea_segunda_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #95a5a6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
            QCheckBox::indicator:checked::after {
                content: "✕";
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.ciptea_segunda_checkbox.stateChanged.connect(self._on_segunda_via_changed)
        self.ciptea_segunda_checkbox.stateChanged.connect(self._check_form_selection)
        checkbox_layout.addWidget(self.ciptea_segunda_checkbox)
        
        # Intermunicipal with VEM option (horizontal layout)
        intermunicipal_container = QWidget()
        intermunicipal_container.setStyleSheet("background-color: transparent;")
        intermunicipal_layout = QHBoxLayout()
        intermunicipal_layout.setContentsMargins(0, 0, 0, 0)
        intermunicipal_layout.setSpacing(20)
        
        self.intermunicipal_checkbox = QCheckBox("Intermunicipal")
        self.intermunicipal_checkbox.setChecked(True)  # Default checked
        self.intermunicipal_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #95a5a6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
            QCheckBox::indicator:checked::after {
                content: "✕";
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.intermunicipal_checkbox.stateChanged.connect(self._on_intermunicipal_changed)
        self.intermunicipal_checkbox.stateChanged.connect(self._check_form_selection)
        intermunicipal_layout.addWidget(self.intermunicipal_checkbox)
        
        # Usar Documento VEM (beside Intermunicipal)
        self.usar_vem_checkbox = QCheckBox("↳ Usar Documento VEM")
        self.usar_vem_checkbox.setEnabled(True)  # Enabled since Intermunicipal is checked by default
        self.usar_vem_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 11px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #95a5a6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
            QCheckBox::indicator:checked::after {
                content: "✕";
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QCheckBox:disabled {
                color: #95a5a6;
            }
            QCheckBox::indicator:disabled {
                background-color: #ecf0f1;
                border-color: #bdc3c7;
            }
        """)
        intermunicipal_layout.addWidget(self.usar_vem_checkbox)
        intermunicipal_layout.addStretch()
        
        intermunicipal_container.setLayout(intermunicipal_layout)
        checkbox_layout.addWidget(intermunicipal_container)
        
        checkbox_widget.setLayout(checkbox_layout)
        layout.addWidget(checkbox_widget)
        
        container.setLayout(layout)
        return container
    
    def _on_primeira_via_changed(self, state):
        """Handle primeira via checkbox change."""
        if state == Qt.Checked and self.ciptea_segunda_checkbox.isChecked():
            # Uncheck segunda via
            self.ciptea_segunda_checkbox.blockSignals(True)
            self.ciptea_segunda_checkbox.setChecked(False)
            self.ciptea_segunda_checkbox.blockSignals(False)
    
    def _on_segunda_via_changed(self, state):
        """Handle segunda via checkbox change."""
        if state == Qt.Checked and self.ciptea_primeira_checkbox.isChecked():
            # Uncheck primeira via
            self.ciptea_primeira_checkbox.blockSignals(True)
            self.ciptea_primeira_checkbox.setChecked(False)
            self.ciptea_primeira_checkbox.blockSignals(False)
    
    def _on_intermunicipal_changed(self, state):
        """Handle intermunicipal checkbox change."""
        # Enable/disable the VEM checkbox based on Intermunicipal state
        if state == Qt.Checked:
            self.usar_vem_checkbox.setEnabled(True)
        else:
            self.usar_vem_checkbox.setEnabled(False)
            self.usar_vem_checkbox.setChecked(False)
    
    def _check_form_selection(self):
        """Check if at least one form is selected and enable/disable button accordingly."""
        # Check both scroll position and form selection
        scrollbar = self.data_scroll_area.verticalScrollBar()
        is_scrolled = scrollbar.value() >= scrollbar.maximum() - 10 or scrollbar.maximum() == 0
        
        has_form_selected = (self.ciptea_primeira_checkbox.isChecked() or 
                            self.ciptea_segunda_checkbox.isChecked() or 
                            self.intermunicipal_checkbox.isChecked())
        
        # Enable button only if both conditions are met
        self.next_btn_page2.setEnabled(is_scrolled and has_form_selected)
    
    def _format_phone_number(self, line_edit):
        """Format phone number as user types: (81) 9 9999-9999"""
        # Get current text and cursor position
        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, text))
        
        # Limit to 11 digits
        digits = digits[:11]
        
        # Format based on length
        formatted = ""
        if len(digits) == 0:
            formatted = ""
        elif len(digits) <= 2:
            formatted = f"({digits}"
        elif len(digits) <= 3:
            formatted = f"({digits[:2]}) {digits[2:]}"
        elif len(digits) <= 7:
            formatted = f"({digits[:2]}) {digits[2:3]} {digits[3:]}"
        else:
            formatted = f"({digits[:2]}) {digits[2:3]} {digits[3:7]}-{digits[7:]}"
        
        # Only update if different to avoid cursor jumps
        if text != formatted:
            # Block signals to prevent recursion
            line_edit.blockSignals(True)
            line_edit.setText(formatted)
            
            # Restore cursor position (at the end is usually best for formatting)
            line_edit.setCursorPosition(len(formatted))
            line_edit.blockSignals(False)
    
    def _format_cpf(self, line_edit):
        """Format CPF as user types: 000.000.000-00"""
        text = line_edit.text()
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, text))
        
        # Limit to 11 digits
        digits = digits[:11]
        
        # Format based on length
        formatted = ""
        if len(digits) == 0:
            formatted = ""
        elif len(digits) <= 3:
            formatted = digits
        elif len(digits) <= 6:
            formatted = f"{digits[:3]}.{digits[3:]}"
        elif len(digits) <= 9:
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:]}"
        else:
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        
        # Only update if different
        if text != formatted:
            line_edit.blockSignals(True)
            line_edit.setText(formatted)
            line_edit.setCursorPosition(len(formatted))
            line_edit.blockSignals(False)
    
    def _format_rg(self, line_edit):
        """Format RG as user types: only numbers (can be RG or CPF format)"""
        text = line_edit.text()
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, text))
        
        # Limit to 11 digits (max CPF length if using CPF as RG)
        digits = digits[:11]
        
        # Only update if different
        if text != digits:
            line_edit.blockSignals(True)
            line_edit.setText(digits)
            line_edit.setCursorPosition(len(digits))
            line_edit.blockSignals(False)
    
    def _format_cep(self, line_edit):
        """Format CEP as user types: 00000-000"""
        text = line_edit.text()
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, text))
        
        # Limit to 8 digits
        digits = digits[:8]
        
        # Format based on length
        formatted = ""
        if len(digits) == 0:
            formatted = ""
        elif len(digits) <= 5:
            formatted = digits
        else:
            formatted = f"{digits[:5]}-{digits[5:]}"
        
        # Only update if different
        if text != formatted:
            line_edit.blockSignals(True)
            line_edit.setText(formatted)
            line_edit.setCursorPosition(len(formatted))
            line_edit.blockSignals(False)
    
    def _format_date(self, line_edit):
        """Format date as user types: DD/MM/AAAA"""
        text = line_edit.text()
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, text))
        
        # Limit to 8 digits
        digits = digits[:8]
        
        # Format based on length
        formatted = ""
        if len(digits) == 0:
            formatted = ""
        elif len(digits) <= 2:
            formatted = digits
        elif len(digits) <= 4:
            formatted = f"{digits[:2]}/{digits[2:]}"
        else:
            formatted = f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"
        
        # Only update if different
        if text != formatted:
            line_edit.blockSignals(True)
            line_edit.setText(formatted)
            line_edit.setCursorPosition(len(formatted))
            line_edit.blockSignals(False)
    
    def _format_uppercase(self, line_edit):
        """Format text to uppercase as user types."""
        text = line_edit.text()
        uppercase_text = text.upper()
        
        # Only update if different
        if text != uppercase_text:
            # Get current cursor position
            cursor_pos = line_edit.cursorPosition()
            
            line_edit.blockSignals(True)
            line_edit.setText(uppercase_text)
            line_edit.setCursorPosition(cursor_pos)
            line_edit.blockSignals(False)
    
    def _show_test_data_menu(self, position):
        """Show context menu for loading test data."""
        menu = QMenu()
        load_test_action = menu.addAction("🧪 Carregar Dados de Teste")
        
        action = menu.exec_(self.next_btn_page1.mapToGlobal(position))
        
        if action == load_test_action:
            self._load_test_data()
    
    def _load_test_data(self):
        """Load test data from data_example.json."""
        try:
            # Load JSON file
            json_path = Path(__file__).parent / "data_example.json"
            
            if not json_path.exists():
                QMessageBox.warning(
                    self,
                    "Arquivo Não Encontrado",
                    f"O arquivo data_example.json não foi encontrado em:\n{json_path}"
                )
                return
            
            with open(json_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # Set the organized files to the test folder
            test_folder = Path(r"C:\Users\Pedro\.auto_preenchedor_data\maria_sophia")
            if test_folder.exists():
                # Map organized files from the test folder
                self.organized_files = {
                    "cpf_do_menor": str(test_folder / "cpf_do_menor.jpg"),
                    "cpf_do_menor_pdf": str(test_folder / "cpf_do_menor.pdf"),
                    "rg_do_menor": str(test_folder / "rg_do_menor.jpg"),
                    "rg_do_menor_pdf": str(test_folder / "rg_do_menor.pdf"),
                    "foto_3x4": str(test_folder / "foto_3x4.jpg"),
                    "cpf_do_responsavel": str(test_folder / "cpf_do_responsavel.jpg"),
                    "cpf_do_responsavel_pdf": str(test_folder / "cpf_do_responsavel.pdf"),
                    "rg_do_responsavel": str(test_folder / "rg_do_responsavel.jpg"),
                    "rg_do_responsavel_pdf": str(test_folder / "rg_do_responsavel.pdf"),
                    "laudo_medico": str(test_folder / "laudo_medico.jpg"),
                    "laudo_medico_pdf": str(test_folder / "laudo_medico.pdf"),
                    "comprovante_residencia": str(test_folder / "comprovante_residencia.jpg"),
                    "comprovante_residencia_pdf": str(test_folder / "comprovante_residencia.pdf"),
                }
            
            # Set beneficiary name
            if "nome_do_menor" in test_data:
                self.name_input.setText(test_data["nome_do_menor"])
            
            # Navigate to data editing page
            self.setWindowTitle("Auto Preenchedor - Verificação de Dados")
            self.stacked_widget.setCurrentIndex(1)
            
            # Populate all fields
            for key, value in test_data.items():
                if key in self.data_fields:
                    field = self.data_fields[key]
                    if isinstance(field, QDateEdit):
                        # Parse date and set QDateEdit
                        if value:
                            try:
                                date_obj = QDate.fromString(str(value), "dd/MM/yyyy")
                                if date_obj.isValid():
                                    field.setDate(date_obj)
                            except:
                                pass
                    else:
                        field.setText(str(value) if value else "")
            
            # Handle CIDs if present
            if "cids" in test_data and test_data["cids"]:
                # First, uncheck all
                for checkbox in self.cid_checkboxes.values():
                    checkbox.setChecked(False)
                
                # Then check those in the test data
                self._set_cid_checkboxes_from_text(test_data["cids"])

            # Update progress label
            self.progress_bar.setVisible(False)
            self.progress_label.setText("🧪 Dados de teste carregados! Verifique e edite se necessário.")
            self.progress_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            
            # Trigger scroll check to enable button if needed
            QTimer.singleShot(100, self._check_scroll_position)
            
            QMessageBox.information(
                self,
                "Dados de Teste Carregados",
                "Os dados de exemplo foram carregados com sucesso!\n\nVocê pode editá-los antes de continuar."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Carregar Dados",
                f"Ocorreu um erro ao carregar os dados de teste:\n\n{str(e)}"
            )
    
    def _open_user_guide(self):
        """Open the user guide in the default browser."""
        import webbrowser
        
        try:
            # Open the GitHub Pages URL
            guide_url = "https://pedrodanadao.github.io/auto_preenchedor_ciptea/"
            webbrowser.open(guide_url)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Abrir Guia",
                f"Ocorreu um erro ao abrir o Guia do Usuário:\n\n{str(e)}"
            )
    
    def _open_organized_folder(self):
        """Open the folder containing organized files."""
        import subprocess
        import os
        
        # Determine the folder to open
        folder_path = None
        
        # If organized_files exists and has entries, use that folder
        if self.organized_files:
            # Get the first file path and extract its parent directory
            first_file = list(self.organized_files.values())[0]
            folder_path = Path(first_file).parent
        else:
            # Use the default auto_preenchedor_data folder
            folder_path = Path.home() / ".auto_preenchedor_data"
        
        # Check if folder exists
        if folder_path and folder_path.exists():
            # Open folder in Windows Explorer
            try:
                os.startfile(str(folder_path))
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Erro ao Abrir Pasta",
                    f"Não foi possível abrir a pasta:\n\n{str(e)}"
                )
        else:
            QMessageBox.information(
                self,
                "Pasta Não Encontrada",
                "A pasta de arquivos organizados ainda não existe.\n\n" +
                "Ela será criada após a extração dos dados dos documentos."
            )
    
    def _show_header_context_menu(self, position):
        """Show context menu when right-clicking the header."""
        menu = QMenu()
        api_key_action = menu.addAction("🔑 Configurar API Key")
        
        action = menu.exec_(self.sender().mapToGlobal(position))
        
        if action == api_key_action:
            self._configure_api_key()
    
    def _configure_api_key(self):
        """Configure the Google API Key in .env file."""
        global GOOGLE_API_KEY
        
        # Get current API key
        current_key = GOOGLE_API_KEY if GOOGLE_API_KEY else ""
        masked_key = current_key[:10] + "..." if len(current_key) > 10 else current_key
        
        # Show input dialog
        new_key, ok = QInputDialog.getText(
            self,
            "Configurar API Key do Google",
            f"API Key atual: {masked_key}\n\nInsira a nova API Key do Google Generative AI:",
            QLineEdit.Normal,
            ""
        )
        
        if ok and new_key.strip():
            try:
                # Path to .env file in the user's .auto_preenchedor_data folder
                data_folder = Path.home() / ".auto_preenchedor_data"
                data_folder.mkdir(parents=True, exist_ok=True)
                env_path = data_folder / ".env"
                
                # Read existing .env content if it exists
                env_content = {}
                if env_path.exists():
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                env_content[key.strip()] = value.strip()
                
                # Update the API key
                env_content['GOOGLE_API_KEY'] = new_key.strip()
                
                # Write back to .env file
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write("# Google Generative AI Configuration\n")
                    for key, value in env_content.items():
                        f.write(f"{key}={value}\n")
                
                # Update the global variable
                GOOGLE_API_KEY = new_key.strip()
                
                QMessageBox.information(
                    self,
                    "API Key Configurada",
                    f"A API Key foi salva com sucesso no arquivo .env!\n\n"
                    f"Localização: {env_path}\n\n"
                    "A chave será carregada automaticamente na próxima execução."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro ao Salvar API Key",
                    f"Ocorreu um erro ao salvar a API Key:\n\n{str(e)}"
                )
    
    def _check_scroll_position(self):
        """Check if user has scrolled to the bottom and enable the next button."""
        # Use the combined check from _check_form_selection
        self._check_form_selection()
    
    def _on_image_changed(self, image_key, file_path):
        """Handle image change event."""
        if file_path:
            self.image_paths[image_key] = file_path
        else:
            self.image_paths.pop(image_key, None)
        
        # Update summary
        count = len(self.image_paths)
        self.summary_label.setText(f"{count}/7 documentos carregados")
    
    def _go_to_next_step(self):
        """Navigate to data extraction page."""
        # Check if name is provided
        beneficiary_name = self.name_input.text().strip()
        if not beneficiary_name:
            QMessageBox.warning(
                self,
                "Aviso",
                "Por favor, digite o nome do beneficiário antes de continuar."
            )
            self.name_input.setFocus()
            return
        
        # Check if at least some documents are loaded
        if len(self.image_paths) == 0:
            QMessageBox.warning(
                self,
                "Aviso",
                "Por favor, carregue pelo menos um documento antes de continuar."
            )
            return
        
        # Switch to data editing page
        self.setWindowTitle("Auto Preenchedor - Verificação de Dados")
        self.stacked_widget.setCurrentIndex(1)
        
        # Scroll to the top of the data editing page
        self.data_scroll_area.verticalScrollBar().setValue(0)
        
        # Start data extraction
        self._extract_data_from_images()
    
    def _go_back_to_documents(self):
        """Go back to document collection page."""
        self.setWindowTitle("Auto Preenchedor - Coleta de Documentos")
        self.stacked_widget.setCurrentIndex(0)
    
    def _start_new_entry(self):
        """Clear all data and start a new entry from the beginning."""
        # Confirm with the user
        reply = QMessageBox.question(
            self,
            "Nova Entrada",
            "Tem certeza que deseja iniciar uma nova entrada?\n\n" +
            "Todos os dados atuais serão perdidos.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Clear all image paths
        self.image_paths = {}
        
        # Clear all drop zones
        self.cpf_beneficiario_zone._clear_image()
        self.rg_beneficiario_zone._clear_image()
        self.foto_3x4_zone._clear_image()
        self.cpf_responsavel_zone._clear_image()
        self.rg_responsavel_zone._clear_image()
        self.laudo_medico_zone._clear_image()
        self.comprovante_residencia_zone._clear_image()
        self.vem_zone._clear_image()
        
        # Clear beneficiary name input
        self.name_input.clear()
        
        # Clear all data fields
        for key, field in self.data_fields.items():
            if isinstance(field, QDateEdit):
                field.setDate(QDate.currentDate())
            else:
                field.clear()
        
        # Uncheck all CID checkboxes
        for checkbox in self.cid_checkboxes.values():
            checkbox.setChecked(False)
        
        # Reset form selection checkboxes to defaults
        self.ciptea_primeira_checkbox.setChecked(True)
        self.ciptea_segunda_checkbox.setChecked(False)
        self.intermunicipal_checkbox.setChecked(True)
        self.usar_vem_checkbox.setChecked(False)
        
        # Clear extracted data and organized files
        self.extracted_data = {}
        self.organized_files = {}
        
        # Reset progress label
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Extraindo dados das imagens...")
        self.progress_label.setStyleSheet("")
        
        # Update summary label
        self.summary_label.setText("0/8 documentos carregados (VEM opcional)")
        
        # Go back to first page
        self.setWindowTitle("Auto Preenchedor")
        self.stacked_widget.setCurrentIndex(0)
    
    def _go_to_form_filling(self):
        """Proceed to form filling."""
        # Check if at least one form is selected
        if not (self.ciptea_primeira_checkbox.isChecked() or 
                self.ciptea_segunda_checkbox.isChecked() or 
                self.intermunicipal_checkbox.isChecked()):
            QMessageBox.warning(
                self,
                "Nenhum Formulário Selecionado",
                "Por favor, selecione pelo menos um formulário para preencher:\n\n" +
                "• CIPTEA Primeira Via\n" +
                "• CIPTEA Segunda Via\n" +
                "• Intermunicipal"
            )
            return
        
        # Collect all data from fields
        self.extracted_data = {}
        for key, field in self.data_fields.items():
            if isinstance(field, QDateEdit):
                self.extracted_data[key] = field.date().toString("dd/MM/yyyy")
            else:
                self.extracted_data[key] = field.text().strip()
        
        # Add selected CIDs to extracted data
        self.extracted_data['cids'] = self.get_selected_cids()
        
        try:
            # Initialize the web driver
            driver = web_automation.open_new_driver()
            
            # Fill Intermunicipal form FIRST (so CIPTEA tabs appear in front)
            if self.intermunicipal_checkbox.isChecked():
                web_automation.fill_intermunicipal_form(driver, self.extracted_data)
                
                # Determine if VEM should be used
                use_vem = self.usar_vem_checkbox.isChecked()
                
                # Attach files to intermunicipal form
                # Map organized files to intermunicipal form keys
                intermunicipal_files = {
                    "rg_menor_pdf": self.organized_files.get("rg_do_menor_pdf", ""),
                    "cpf_menor_pdf": self.organized_files.get("cpf_do_menor_pdf", ""),
                    "comprovante_residencia_pdf": self.organized_files.get("comprovante_residencia_pdf", ""),
                    "foto_3x4": self.organized_files.get("foto_3x4", ""),
                    "laudo_medico_pdf": self.organized_files.get("laudo_medico_pdf", ""),
                    "rg_do_responsavel_pdf": self.organized_files.get("rg_do_responsavel_pdf", ""),
                    "cpf_do_responsavel_pdf": self.organized_files.get("cpf_do_responsavel_pdf", ""),
                    "vem_jpg": self.organized_files.get("vem", "")
                }
                web_automation.attach_intermunicipal_files(driver, intermunicipal_files, use_vem=use_vem)
            
            # Fill CIPTEA Primeira Via
            if self.ciptea_primeira_checkbox.isChecked():
                web_automation.fill_cipteape_form(
                    driver, 
                    self.extracted_data, 
                    self.organized_files, 
                    primeira_via=True
                )
            
            # Fill CIPTEA Segunda Via
            if self.ciptea_segunda_checkbox.isChecked():
                web_automation.fill_cipteape_form(
                    driver, 
                    self.extracted_data, 
                    self.organized_files, 
                    primeira_via=False
                )
            
            # Success message
            QMessageBox.information(
                self,
                "Preenchimento Concluído",
                "Os formulários foram preenchidos com sucesso!\n\n" +
                "Por favor, revise os dados no navegador antes de submeter."
            )
            
        except Exception as e:
            # Error handling
            QMessageBox.critical(
                self,
                "Erro no Preenchimento",
                f"Ocorreu um erro ao preencher os formulários:\n\n{str(e)}\n\n" +
                "Por favor, preencha os formulários manualmente ou tente novamente."
            )
    
    def _extract_data_from_images(self):
        """Extract data from images and populate fields."""
        try:
            # Show progress
            self.progress_label.setText("Organizando arquivos...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            QApplication.processEvents()  # Force UI update
            
            # Get beneficiary name
            beneficiary_name = self.name_input.text().strip()
            
            # Step 1: Handle missing CPF/RG pairs by duplicating
            # If only CPF or only RG is provided, use it for both
            image_paths_to_organize = self.image_paths.copy()
            
            # Check beneficiary documents
            if "cpf_do_menor" in image_paths_to_organize and "rg_do_menor" not in image_paths_to_organize:
                image_paths_to_organize["rg_do_menor"] = image_paths_to_organize["cpf_do_menor"]
            elif "rg_do_menor" in image_paths_to_organize and "cpf_do_menor" not in image_paths_to_organize:
                image_paths_to_organize["cpf_do_menor"] = image_paths_to_organize["rg_do_menor"]
            
            # Check responsible documents
            if "cpf_do_responsavel" in image_paths_to_organize and "rg_do_responsavel" not in image_paths_to_organize:
                image_paths_to_organize["rg_do_responsavel"] = image_paths_to_organize["cpf_do_responsavel"]
            elif "rg_do_responsavel" in image_paths_to_organize and "cpf_do_responsavel" not in image_paths_to_organize:
                image_paths_to_organize["cpf_do_responsavel"] = image_paths_to_organize["rg_do_responsavel"]
            
            # Step 2: Organize image files into folder
            self.organized_files = image_processor.organize_image_files(
                image_paths_to_organize, 
                beneficiary_name
            )
            
            # Step 3: Create collage from all images for OCR
            self.progress_label.setText("Criando colagem de imagens...")
            QApplication.processEvents()
            
            # Get all image paths (not PDFs), excluding foto_3x4 and vem since they don't have relevant data
            image_paths_for_collage = [
                path for key, path in self.organized_files.items() 
                if not key.endswith('_pdf') and key not in ['foto_3x4', 'vem']
            ]
            
            # Create collage in the same folder
            folder_path = Path(self.organized_files[list(self.organized_files.keys())[0]]).parent
            collage_path = folder_path / "collage.jpg"
            
            # Calculate grid size (3 columns, enough rows)
            num_images = len(image_paths_for_collage)
            cols = 3
            rows = (num_images + cols - 1) // cols  # Ceiling division
            
            image_processor.create_image_collage(
                image_paths_for_collage,
                str(collage_path),
                rows,
                cols,
                image_size=(1500, 1500)
            )
            
            # Step 4: Extract text from collage using AI
            self.progress_label.setText("Extraindo texto das imagens com IA...")
            QApplication.processEvents()
            
            extracted_text = data_extractor.get_image_text(
                str(collage_path),
                GOOGLE_API_KEY
            )
            
            # Step 5: Parse text into structured data
            self.progress_label.setText("Processando dados extraídos...")
            QApplication.processEvents()
            
            self.extracted_data = data_extractor.get_data_from_text(
                extracted_text,
                GOOGLE_API_KEY
            )
            
            # Step 6: Populate fields with extracted data
            if self.extracted_data:
                # Add missing fields with empty values
                all_fields = [
                    "nome_do_responsavel", "nome_do_menor", "nome_da_mae_do_menor",
                    "cpf_do_responsavel", "rg_do_responsavel", "cpf_do_menor", "rg_do_menor",
                    "data_de_nascimento_do_menor", "endereço", "cep", "telefone", "email"
                ]
                
                for field in all_fields:
                    if field not in self.extracted_data:
                        self.extracted_data[field] = ""
                
                # Populate UI fields (except CIDs)
                for key, value in self.extracted_data.items():
                    if key in self.data_fields:
                        field = self.data_fields[key]
                        if isinstance(field, QDateEdit):
                            # Parse date and set QDateEdit
                            if value:
                                try:
                                    date_obj = QDate.fromString(str(value), "dd/MM/yyyy")
                                    if date_obj.isValid():
                                        field.setDate(date_obj)
                                except:
                                    pass
                        else:
                            field.setText(str(value) if value else "")
                
                # Handle CIDs separately - check boxes based on extracted data
                if "cids" in self.extracted_data and self.extracted_data["cids"]:
                    self._set_cid_checkboxes_from_text(self.extracted_data["cids"])
                
                # Success message
                self.progress_bar.setVisible(False)
                self.progress_label.setText("✓ Dados extraídos! Verifique e edite se necessário.")
                self.progress_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                
                # Trigger scroll check to enable button if needed
                QTimer.singleShot(100, self._check_scroll_position)
            else:
                raise Exception("Não foi possível extrair dados estruturados do texto.")
                
        except Exception as e:
            # Handle errors
            self.progress_bar.setVisible(False)
            self.progress_label.setText("✗ Erro na extração de dados")
            self.progress_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
            QMessageBox.critical(
                self,
                "Erro na Extração",
                f"Ocorreu um erro ao extrair os dados:\n\n{str(e)}\n\nPor favor, preencha os campos manualmente."
            )
            
            # Fill with basic data
            self.data_fields["nome_do_menor"].setText(beneficiary_name)
    
    def _set_cid_checkboxes_from_text(self, cids_list):
        """Check matching checkboxes based on a list of CIDs that are available in web forms.
        
        Args:
            cids_list (list): List of CID codes (e.g., ['10 F84.0', '11 6A02'])
        """
        if not cids_list:
            return
        
        # Use web_automation function to get valid CIDs
        valid_cid_options = web_automation.get_best_guess_cids(cids_list)
        
        if not valid_cid_options:
            return
        
        # Map CID_OPTIONS to checkbox keys
        # CID_OPTIONS format: "cid10_F84_0", "cid11_6A02_0"
        # Checkbox keys format: "10:F84.0", "11:6A02.0"
        for cid_option in valid_cid_options:
            if cid_option.startswith('cid10_'):
                # Extract F84_X and convert to F84.X
                parts = cid_option.replace('cid10_', '').replace('_', '.')
                checkbox_key = f"10:{parts}"
            elif cid_option.startswith('cid11_'):
                # Extract FA02_X and convert to 6A02.X
                parts = cid_option.replace('cid11_6A02_', '').replace('_', '.')
                checkbox_key = f"11:6A02.{parts}"
            else:
                continue
            
            if checkbox_key in self.cid_checkboxes:
                self.cid_checkboxes[checkbox_key].setChecked(True)

    
    def get_selected_cids(self):
        """Get list of selected CID codes."""
        selected_cids = []
        for cid_code, checkbox in self.cid_checkboxes.items():
            if checkbox.isChecked():
                selected_cids.append(cid_code)
        return selected_cids
    
    def get_beneficiary_name(self):
        """Get the beneficiary name from input field."""
        return self.name_input.text().strip()
    
    def get_image_paths(self):
        """Get all collected image paths."""
        return self.image_paths.copy()
    
    def get_extracted_data(self):
        """Get all extracted and edited data."""
        data = {}
        for key, field in self.data_fields.items():
            # Handle QDateEdit differently
            if isinstance(field, QDateEdit):
                data[key] = field.date().toString("dd/MM/yyyy")
            else:
                data[key] = field.text().strip()
        
        # Add selected CIDs
        data['cids'] = self.get_selected_cids()
        
        return data


def main():
    """Run the UI application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = AutoPreenchedorUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
