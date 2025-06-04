import os
import glob
import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QSettings

def select_run_directory(self):
    settings = QSettings("MeuProjeto", "iLOGGER Mangue Baja")
    last_dir = settings.value("last_run_directory", os.path.expanduser("~"))
    directory = QFileDialog.getExistingDirectory(self, "Selecione o diretório", last_dir)
    if directory:
        self.txt_run_directory.setText(directory)
        settings.setValue("last_run_directory", directory)

def select_save_directory(self):
    settings = QSettings("MeuProjeto", "iLOGGER Mangue Baja")
    last_dir = settings.value("last_save_directory", os.path.expanduser("~"))
    directory = QFileDialog.getExistingDirectory(self, "Selecione o diretório para salvar", last_dir)
    if directory:
        self.txt_save_directory.setText(directory)
        settings.setValue("last_save_directory", directory)

def select_plot_files(self):
    settings = QSettings("MeuProjeto", "iLOGGER Mangue Baja")
    last_dir = settings.value("last_plot_directory", os.path.expanduser("~"))
    filenames, _ = QFileDialog.getOpenFileNames(self, "Selecione os arquivos", last_dir, "CSV files (*.csv)")
    if filenames:
        self.list_files.clear()
        self.list_files.addItems(filenames)
        # Salva o diretório do primeiro arquivo selecionado
        settings.setValue("last_plot_directory", os.path.dirname(filenames[0]))

def generate_csv(self):
    run_directory = self.txt_run_directory.text()
    run_number = self.txt_run_number.text().strip()

    if not run_directory:
        QMessageBox.warning(self, "Erro", "Selecione o diretório das RUNs.")
        return

    if not run_number:
        QMessageBox.warning(self, "Erro", "Digite o número da RUN.")
        return

    run_files = glob.glob(os.path.join(run_directory, f"*RUN{run_number}*.csv"))
    if not run_files:
        QMessageBox.warning(self, "Erro", f"Nenhum arquivo encontrado para a RUN {run_number}.")
        return

    run_file = run_files[0]
    save_directory = self.txt_save_directory.text()
    if not save_directory:
        QMessageBox.warning(self, "Erro", "Selecione o diretório de salvamento.")
        return

    save_path = os.path.join(save_directory, f"RUN{run_number}_processed.csv")
    try:
        df = pd.read_csv(run_file)
        df.to_csv(save_path, index=False)
        QMessageBox.information(self, "Sucesso", f"Arquivo CSV gerado em: {save_path}")
    except Exception as e:
        QMessageBox.critical(self, "Erro", f"Erro ao gerar o CSV: {str(e)}")

