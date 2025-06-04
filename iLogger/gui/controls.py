from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout, QLabel, QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
from operations.file_operations import select_run_directory, select_save_directory, select_plot_files, generate_csv

def create_setup_group(parent):
    group = QGroupBox("Setup do Veículo", parent)
    layout = QGridLayout()
    group.setLayout(layout)
    inputs = [
        ("RPM do Motor (Baixa):", "txt_rpm_baixa"),
        ("RPM do Motor (Alta):", "txt_rpm_alta"),
        ("Peso na CVT (gramas):", "txt_peso_cvt"),
        ("Constante da Mola (N/m):", "txt_constante_mola"),
        ("Angulação da Rampa (graus):", "txt_angulacao_rampa"),
        ("Data:", "txt_data")
    ]
    for i, (label, attr) in enumerate(inputs):
        widget = QLineEdit(parent)
        setattr(parent, attr, widget)
        layout.addWidget(QLabel(label), i, 0)
        layout.addWidget(widget, i, 1)
    return group

def create_files_group(parent):
    group = QGroupBox("Seleção de Arquivos", parent)
    layout = QGridLayout()
    group.setLayout(layout)
    inputs = [
        ("Diretório das RUNs:", "txt_run_directory", "btn_run_directory", select_run_directory),
        ("Número da RUN:", "txt_run_number", None, None),
        ("Diretório de Salvamento:", "txt_save_directory", "btn_save_directory", select_save_directory),
        ("Furos no Disco de Freio:", "txt_furos", None, None)
    ]
    for i, (label, txt_attr, btn_attr, slot) in enumerate(inputs):
        widget = QLineEdit(parent)
        setattr(parent, txt_attr, widget)
        layout.addWidget(QLabel(label), i, 0)
        layout.addWidget(widget, i, 1)
        if btn_attr:
            btn = QPushButton("Procurar", parent)
            btn.clicked.connect(slot.__get__(parent))
            setattr(parent, btn_attr, btn)
            layout.addWidget(btn, i, 2)
    # Lista de arquivos e botão para selecionar
    parent.list_files = QListWidget(parent)
    btn_select = QPushButton("Selecionar Arquivos", parent)
    btn_select.clicked.connect(select_plot_files.__get__(parent))
    layout.addWidget(QLabel("Arquivos Selecionados:"), 4, 0)
    layout.addWidget(btn_select, 4, 1)
    layout.addWidget(parent.list_files, 5, 0, 1, 3)
    return group

def create_actions_group(parent):
    group = QGroupBox("Ações", parent)
    layout = QVBoxLayout()
    group.setLayout(layout)
    buttons = [
        ("Gerar CSV", generate_csv),
        # Outras ações como plotar gráficos e salvar PDF serão adicionadas no módulo de gráficos
    ]
    for label, slot in buttons:
        btn = QPushButton(label, parent)
        btn.clicked.connect(slot.__get__(parent))
        layout.addWidget(btn)
    return group

def create_observations_group(parent):
    group = QGroupBox("Observações", parent)
    layout = QVBoxLayout()
    group.setLayout(layout)
    parent.txt_observation = QTextEdit(parent)
    parent.txt_observation.setPlaceholderText("Insira observações adicionais aqui...")
    layout.addWidget(parent.txt_observation)
    return group

def create_controls_panel(parent):
    panel = QWidget(parent)
    layout = QVBoxLayout(panel)
    # Cria grupos e organiza em layout horizontal
    upper_layout = QHBoxLayout()
    upper_layout.addWidget(create_setup_group(parent))
    upper_layout.addWidget(create_files_group(parent))
    upper_layout.addWidget(create_actions_group(parent))
    layout.addLayout(upper_layout)
    layout.addWidget(create_observations_group(parent))
    return panel
