import sys
import os
import math
import pandas as pd
import numpy as np
import concurrent.futures
import matplotlib.pyplot as plt
from scipy import signal

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QTabWidget, QListWidget,
    QTextEdit, QSplitter, QComboBox, QGridLayout, QGroupBox, QToolBar,
    QApplication, QCheckBox
)
from PyQt6.QtGui import QIcon, QFont, QAction
from PyQt6.QtCore import Qt, QSettings

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_pdf import PdfPages

from operations.file_operations import (
    select_run_directory, select_save_directory,
    select_plot_files, generate_csv
)
from operations.plotting_operations import (
    plot_graphs, update_custom_plot, plot_relation,
    add_statistics_to_plots, plot_comparison_graphs,
    plot_bar_with_values, plot_metrics_table, clear_plots,
    update_axis_comboboxes
)
from operations.pdf_operations import save_pdf, save_pdf_drive
from qt_material import apply_stylesheet

class MainWindow(QMainWindow):
    def __init__(self):
        # Inicializa atributos dos gráficos
        self.fig_rot = None
        self.fig_vel = None
        self.fig_rel = None
        self.fig_acc = None
        self.fig_decel = None
        self.fig_dist = None
        self.fig_comparison = None
        self.fig_custom = None
        self.fig_metrics_table = None
        self.axis_data = {}

        super().__init__()
        self.setWindowTitle("MANGUE LOGGER")
        self.setWindowIcon(QIcon("icone_window.png"))
        self.resize(1200, 900)
        self.settings = QSettings("MeuProjeto", "MANGUE LOGGER")
        self.current_theme = "dark_teal.xml"  # Tema inicial
        self._init_ui()

    def _init_ui(self):
        self._create_toolbar()
        self._create_central_widget()
        self._create_tabs()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Ações")
        self.addToolBar(self.toolbar)

        toggle_theme_action = QAction("Alternar Tema", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        self.toolbar.addAction(toggle_theme_action)

        save_pdf_drive_action = QAction("Salvar PDF no Google Drive", self)
        save_pdf_drive_action.triggered.connect(self.save_pdf_drive)
        self.toolbar.addAction(save_pdf_drive_action)

    def _create_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self.header_label = QLabel("MANGUE LOGGER")
        header_font = QFont("Segoe UI", 720, QFont.Weight.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.header_label)

    def _create_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.main_layout.addWidget(self.tab_widget)

        self._init_controls_tab()
        self._init_graphs_tab()
        self._init_dashboard_tab()

    def toggle_theme(self):
        """Alterna entre dois temas via qt-material."""
        app = QApplication.instance()
        self.current_theme = "light_blue.xml" if self.current_theme == "dark_teal.xml" else "dark_teal.xml"
        apply_stylesheet(app, theme=self.current_theme)

    # ----- Aba de Controles -----
    def _init_controls_tab(self):
        self.controls_tab = QWidget()
        controls_layout = QVBoxLayout(self.controls_tab)
        controls_layout.setSpacing(15)
        self.tab_widget.addTab(self.controls_tab, "Controles")

        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(20)
        controls_layout.addLayout(groups_layout)

        groups_layout.addWidget(self._create_setup_group())
        groups_layout.addWidget(self._create_files_group())
        groups_layout.addWidget(self._create_actions_group())
        controls_layout.addWidget(self._create_observations_group())

    def _create_setup_group(self):
        group = QGroupBox("Setup do Veículo")
        layout = QGridLayout(group)
        inputs = [
            ("RPM do Motor (Baixa):", "txt_rpm_baixa"),
            ("RPM do Motor (Alta):", "txt_rpm_alta"),
            ("Peso na CVT (gramas):", "txt_peso_cvt"),
            ("Constante da Mola (N/m):", "txt_constante_mola"),
            ("Angulação da Rampa (graus):", "txt_angulacao_rampa"),
            ("Data:", "txt_data")
        ]
        for i, (label_text, attr) in enumerate(inputs):
            label = QLabel(label_text)
            line_edit = QLineEdit()
            setattr(self, attr, line_edit)
            layout.addWidget(label, i, 0)
            layout.addWidget(line_edit, i, 1)
        return group

    def _create_files_group(self):
        group = QGroupBox("Seleção de Arquivos")
        layout = QGridLayout(group)
        inputs = [
            ("Diretório das RUNs:", "txt_run_directory", "btn_run_directory", select_run_directory),
            ("Número da RUN:", "txt_run_number", None, None),
            ("Diretório de Salvamento:", "txt_save_directory", "btn_save_directory", select_save_directory),
            ("Furos no Disco de Freio:", "txt_furos", None, None)
        ]
        for i, (label_text, txt_attr, btn_attr, slot) in enumerate(inputs):
            label = QLabel(label_text)
            line_edit = QLineEdit()
            setattr(self, txt_attr, line_edit)
            layout.addWidget(label, i, 0)
            layout.addWidget(line_edit, i, 1)
            if btn_attr:
                btn = QPushButton("Procurar")
                btn.clicked.connect(slot.__get__(self))
                setattr(self, btn_attr, btn)
                layout.addWidget(btn, i, 2)
        self.list_files = QListWidget()
        self.btn_select_files = QPushButton("Selecionar Arquivos")
        self.btn_select_files.clicked.connect(select_plot_files.__get__(self))
        layout.addWidget(QLabel("Arquivos Selecionados:"), 4, 0)
        layout.addWidget(self.btn_select_files, 4, 1)
        layout.addWidget(self.list_files, 5, 0, 1, 3)
        return group

    def _create_actions_group(self):
        group = QGroupBox("Ações")
        layout = QVBoxLayout(group)
        buttons = [
            ("Gerar CSV", generate_csv),
            ("Plotar Gráficos", plot_graphs),
            ("Salvar Gráficos", self.save_graphs),
            ("Salvar em PDF", save_pdf)
        ]
        for label, slot in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(slot.__get__(self))
            layout.addWidget(btn)
        return group

    def _create_observations_group(self):
        group = QGroupBox("Observações")
        layout = QVBoxLayout(group)
        self.txt_observation = QTextEdit()
        self.txt_observation.setPlaceholderText("Insira observações adicionais aqui...")
        layout.addWidget(self.txt_observation)
        return group

    # ----- Aba de Gráficos -----
    def _init_graphs_tab(self):
        self.graphs_tab = QWidget()
        graphs_layout = QVBoxLayout(self.graphs_tab)
        graphs_layout.setSpacing(10)
        self.tab_widget.addTab(self.graphs_tab, "Gráficos")

        self.plots_tab_widget = QTabWidget()
        graphs_layout.addWidget(self.plots_tab_widget)

        # Aba de estatísticas e comparação
        self._init_stats_tab()
        self._init_custom_plot_tab()

    def _init_stats_tab(self):
        self.stats_widget = QWidget()
        stats_layout = QHBoxLayout(self.stats_widget)

        self.text_stats = QTextEdit()
        self.text_stats.setReadOnly(True)
        stats_layout.addWidget(self.text_stats)

        self.splitter = QSplitter()
        self.splitter.addWidget(self.text_stats)

        self.fig_comparison = plt.figure(figsize=(12, 10), dpi=100)
        self.canvas_comparison = FigureCanvas(self.fig_comparison)
        self.splitter.addWidget(self.canvas_comparison)
        stats_layout.addWidget(self.splitter)

        self.plots_tab_widget.addTab(self.stats_widget, "Estatísticas e Comparação")

    def _init_custom_plot_tab(self):
        self.custom_plot_widget = QWidget()
        layout = QVBoxLayout(self.custom_plot_widget)

        axis_layout = QGridLayout()
        self.label_x = QLabel("Eixo X:")
        self.combo_x = QComboBox()
        self.label_y = QLabel("Eixo Y:")
        self.combo_y = QComboBox()
        self.label_z = QLabel("Eixo Z (Opcional):")
        self.combo_z = QComboBox()
        self.combo_z.addItem("")
        axis_layout.addWidget(self.label_x, 0, 0)
        axis_layout.addWidget(self.combo_x, 0, 1)
        axis_layout.addWidget(self.label_y, 1, 0)
        axis_layout.addWidget(self.combo_y, 1, 1)
        axis_layout.addWidget(self.label_z, 2, 0)
        axis_layout.addWidget(self.combo_z, 2, 1)

        self.btn_update_custom_plot = QPushButton("Atualizar Gráfico")
        self.btn_update_custom_plot.setFixedWidth(180)
        self.btn_update_custom_plot.clicked.connect(update_custom_plot.__get__(self))
        axis_layout.addWidget(self.btn_update_custom_plot, 3, 0, 1, 2)

        layout.addLayout(axis_layout)

        self.fig_custom = plt.figure(figsize=(12, 8), dpi=100)
        self.canvas_custom = FigureCanvas(self.fig_custom)
        layout.addWidget(self.canvas_custom)

        self.plots_tab_widget.addTab(self.custom_plot_widget, "Gráfico Personalizado")

    # ----- Aba de Dashboard Interativo -----
    def _init_dashboard_tab(self):
        self.dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(self.dashboard_tab)

        # Seção de seleção dos gráficos a serem exibidos
        selection_group = QGroupBox("Seleção de Gráficos para Dashboard")
        selection_layout = QHBoxLayout(selection_group)
        self.dashboard_checkboxes = {}
        graph_options = [
            "Rotação do Motor",
            "Velocidade",
            "Relação RPM x Velocidade",
            "Aceleração",
            "Desaceleração",
            "Distância Percorrida"
        ]
        for option in graph_options:
            cb = QCheckBox(option)
            cb.setChecked(True)
            self.dashboard_checkboxes[option] = cb
            selection_layout.addWidget(cb)
        dashboard_layout.addWidget(selection_group)

        # Botão para atualizar o dashboard
        self.btn_update_dashboard = QPushButton("Atualizar Dashboard")
        self.btn_update_dashboard.clicked.connect(self.update_dashboard)
        dashboard_layout.addWidget(self.btn_update_dashboard)
        
        # Área de exibição dos gráficos (dashboard)
        self.fig_dashboard = plt.figure(figsize=(14, 9), dpi=100)
        self.canvas_dashboard = FigureCanvas(self.fig_dashboard)
        dashboard_layout.addWidget(self.canvas_dashboard)

        self.tab_widget.addTab(self.dashboard_tab, "Dashboard Interativo")

    def update_dashboard(self):
        """Atualiza o dashboard com os gráficos selecionados pelo usuário."""
        if not self.axis_data:
            QMessageBox.warning(self, "Erro", "Dados não disponíveis. Execute a geração de gráficos primeiro.")
            return

        selected_graphs = [name for name, cb in self.dashboard_checkboxes.items() if cb.isChecked()]
        if not selected_graphs:
            QMessageBox.warning(self, "Erro", "Selecione ao menos um gráfico para exibir.")
            return

        self.fig_dashboard.clear()
        n = len(selected_graphs)
        ncols = math.ceil(math.sqrt(n))
        nrows = math.ceil(n / ncols)

        for i, graph in enumerate(selected_graphs):
            ax = self.fig_dashboard.add_subplot(nrows, ncols, i + 1)
            if graph == "Rotação do Motor":
                ax.plot(self.axis_data.get("Tempo (s)", []), self.axis_data.get("RPM", []), label="RPM")
                ax.set_xlabel("Tempo (s)")
                ax.set_ylabel("RPM")
                ax.set_title("Rotação do Motor")
            elif graph == "Velocidade":
                ax.plot(self.axis_data.get("Tempo (s)", []), self.axis_data.get("Velocidade (Km/h)", []),
                        label="Velocidade", color='orange')
                ax.set_xlabel("Tempo (s)")
                ax.set_ylabel("Velocidade (Km/h)")
                ax.set_title("Velocidade")
            elif graph == "Relação RPM x Velocidade":
                ax.plot(self.axis_data.get("Velocidade (Km/h)", []), self.axis_data.get("RPM", []),
                        label="Relação", color='magenta')
                ax.set_xlabel("Velocidade (Km/h)")
                ax.set_ylabel("RPM")
                ax.set_title("Relação RPM x Velocidade")
            elif graph == "Aceleração":
                ax.plot(self.axis_data.get("Tempo (s)", [])[:-1], self.axis_data.get("Aceleração (m/s²)", []),
                        label="Aceleração", color='green')
                ax.set_xlabel("Tempo (s)")
                ax.set_ylabel("Aceleração (m/s²)")
                ax.set_title("Aceleração")
            elif graph == "Desaceleração":
                ax.plot(self.axis_data.get("Tempo (s)", [])[:-1], self.axis_data.get("Desaceleração (m/s²)", []),
                        label="Desaceleração", color='red')
                ax.set_xlabel("Tempo (s)")
                ax.set_ylabel("Desaceleração (m/s²)")
                ax.set_title("Desaceleração")
            elif graph == "Distância Percorrida":
                ax.plot(self.axis_data.get("Tempo (s)", []), self.axis_data.get("Distância (m)", []),
                        label="Distância", color='purple')
                ax.set_xlabel("Tempo (s)")
                ax.set_ylabel("Distância (m)")
                ax.set_title("Distância Percorrida")
            ax.legend()
            ax.grid(True)

        self.fig_dashboard.tight_layout()
        self.canvas_dashboard.draw()

    def save_graphs(self):
        if self.plots_tab_widget.count() == 0:
            QMessageBox.warning(self, "Aviso", "Nenhum gráfico para salvar.")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Selecione o diretório para salvar os gráficos")
        if not save_dir:
            return

        fig_width, fig_height, dpi_value = 14, 9, 100

        for i in range(self.plots_tab_widget.count()):
            tab_name = self.plots_tab_widget.tabText(i)
            canvas = self.plots_tab_widget.widget(i)
            if hasattr(canvas, 'figure'):
                fig = canvas.figure
                fig.set_size_inches(fig_width, fig_height)
                fig.tight_layout()
                save_path = os.path.join(save_dir, f"{tab_name}.png")
                fig.savefig(save_path, dpi=dpi_value, bbox_inches='tight')
                print(f"Gráfico salvo em: {save_path}")

        QMessageBox.information(self, "Sucesso", "Gráficos salvos com sucesso!")

    def save_pdf_drive(self):
        save_pdf_drive(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
