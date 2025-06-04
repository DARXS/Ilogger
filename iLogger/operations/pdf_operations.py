import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QSettings
import datetime

def save_pdf(self):
    if self.plots_tab_widget.count() == 0:
        QMessageBox.warning(self, "Aviso", "Nenhum gráfico para salvar.")
        return

    save_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF files (*.pdf)")
    if not save_path:
        return

    _save_pdf_to_path(self, save_path)

def save_pdf_drive(self):
    settings = QSettings("MeuProjeto", "MANGUE LOGGER")
    google_drive_path = settings.value("google_drive_path", "")
    if not google_drive_path:
        google_drive_path = QFileDialog.getExistingDirectory(self, "Selecione a pasta do Google Drive", os.path.expanduser("~"))
        if not google_drive_path:
            return
        settings.setValue("google_drive_path", google_drive_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(google_drive_path, f"iLOGGER_MangueBaja_{timestamp}.pdf")
    _save_pdf_to_path(self, save_path)

def _save_pdf_to_path(self, save_path):
    with PdfPages(save_path) as pdf:
        # CAPA DO RELATÓRIO COM IMAGEM
        capa_path = "CAPA.jpg"  # Caminho da imagem da capa
        if os.path.exists(capa_path):
            fig_cover, ax_cover = plt.subplots(figsize=(14, 9), dpi=600)
            ax_cover.axis('off')
            img = mpimg.imread(capa_path)
            ax_cover.imshow(img)
            pdf.savefig(fig_cover, bbox_inches='tight')
            plt.close(fig_cover)
        fig_setup, ax_setup = plt.subplots(figsize=(14, 9))
        ax_setup.axis('off')

        setup_data = [
            ["RPM do Motor (Baixa)", self.txt_rpm_baixa.text()],
            ["RPM do Motor (Alta)", self.txt_rpm_alta.text()],
            ["Peso na CVT (gramas)", self.txt_peso_cvt.text()],
            ["Constante da Mola (N/m)", self.txt_constante_mola.text()],
            ["Angulação da Rampa (graus)", self.txt_angulacao_rampa.text()],
            ["Data", self.txt_data.text()]
        ]
        setup_table = ax_setup.table(
            cellText=setup_data,
            colLabels=["Configuração", "Valor"],
            loc='center',
            cellLoc='center',
            bbox=[0.25, 0.1, 0.5, 0.8]
        )

        setup_table.auto_set_font_size(False)
        setup_table.set_fontsize(10)
        setup_table.scale(1.2, 1.2)

        ax_setup.set_title("Setup do Veículo", fontsize=14, pad=20)
        pdf.savefig(fig_setup, bbox_inches='tight')
        plt.close(fig_setup)

        # SEGUNDA PÁGINA: Tabela de Métricas e Variações
        if hasattr(self, 'fig_metrics_table'):
            fig_metrics, ax_metrics = plt.subplots(figsize=(14, 9))
            ax_metrics.axis('off')

            stats_data = {
                'Arquivo': [stats['file'] for stats in self.all_stats],
                'Vel. Máx (Km/h)': [round(stats['max_vel'], 2) for stats in self.all_stats],
                'RPM Máx': [round(stats['max_rpm'], 2) for stats in self.all_stats],
                'Vel. Média (Km/h)': [round(stats['avg_vel'], 2) for stats in self.all_stats],
                'RPM Médio': [round(stats['avg_rpm'], 2) for stats in self.all_stats],
                'Acel. Máx (m/s²)': [round(stats['max_acc'], 2) for stats in self.all_stats],
                'Acel. Média (m/s²)': [round(stats['avg_acc'], 2) for stats in self.all_stats],
                'Desac. Máx (m/s²)': [round(stats['max_decel'], 2) for stats in self.all_stats],
                'Desac. Média (m/s²)': [round(stats['avg_decel'], 2) for stats in self.all_stats],
                'Distância Total (m)': [round(stats['distancia_total'], 2) for stats in self.all_stats]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.set_index('Arquivo', inplace=True)

            table_metrics = ax_metrics.table(
                cellText=stats_df.values,
                colLabels=stats_df.columns,
                rowLabels=stats_df.index,
                loc='center',
                cellLoc='center',
                bbox=[0.1, 0.6, 1.5, 0.3]
            )

            table_metrics.auto_set_font_size(False)
            table_metrics.set_fontsize(10)
            table_metrics.scale(1.2, 1.2)

            ax_metrics.text(0.5, 0.95, "Tabela de Métricas", fontsize=14, ha='center', va='center')

            if len(stats_df) > 1:
                first_file_stats = stats_df.iloc[0]
                variations = []

                for i in range(1, len(stats_df)):
                    file_stats = stats_df.iloc[i]
                    variation = {
                        'Arquivo': stats_df.index[i],
                        'Δ Vel. Máx (%)': ((file_stats['Vel. Máx (Km/h)'] - first_file_stats['Vel. Máx (Km/h)']) / first_file_stats['Vel. Máx (Km/h)']) * 100,
                        'Δ RPM Máx (%)': ((file_stats['RPM Máx'] - first_file_stats['RPM Máx']) / first_file_stats['RPM Máx']) * 100,
                        'Δ Vel. Média (%)': ((file_stats['Vel. Média (Km/h)'] - first_file_stats['Vel. Média (Km/h)']) / first_file_stats['Vel. Média (Km/h)']) * 100,
                        'Δ RPM Médio (%)': ((file_stats['RPM Médio'] - first_file_stats['RPM Médio']) / first_file_stats['RPM Médio']) * 100,
                        'Δ Acel. Máx (%)': ((file_stats['Acel. Máx (m/s²)'] - first_file_stats['Acel. Máx (m/s²)']) / first_file_stats['Acel. Máx (m/s²)']) * 100,
                        'Δ Acel. Média (%)': ((file_stats['Acel. Média (m/s²)'] - first_file_stats['Acel. Média (m/s²)']) / first_file_stats['Acel. Média (m/s²)']) * 100,
                        'Δ Desac. Máx (%)': ((file_stats['Desac. Máx (m/s²)'] - first_file_stats['Desac. Máx (m/s²)']) / first_file_stats['Desac. Máx (m/s²)']) * 100,
                        'Δ Desac. Média (%)': ((file_stats['Desac. Média (m/s²)'] - first_file_stats['Desac. Média (m/s²)']) / first_file_stats['Desac. Média (m/s²)']) * 100,
                        'Δ Distância Total (%)': ((file_stats['Distância Total (m)'] - first_file_stats['Distância Total (m)']) / first_file_stats['Distância Total (m)']) * 100
                    }
                    variations.append(variation)

                variations_df = pd.DataFrame(variations)
                variations_df.set_index('Arquivo', inplace=True)
                variations_df = variations_df.round(2)

                table_variations = ax_metrics.table(
                    cellText=variations_df.values,
                    colLabels=variations_df.columns,
                    rowLabels=variations_df.index,
                    loc='center',
                    cellLoc='center',
                    bbox=[0.1, 0.1, 1.5, 0.3]
                )

                table_variations.auto_set_font_size(False)
                table_variations.set_fontsize(10)
                table_variations.scale(1.2, 1.2)

                ax_metrics.text(0.5, 0.45, "Variações Estatísticas em Relação ao Primeiro Arquivo", fontsize=14, ha='center', va='center')

            pdf.savefig(fig_metrics, bbox_inches='tight')
            plt.close(fig_metrics)

        # TERCEIRA PÁGINA: Observações e Estatísticas
        fig_text, ax_text = plt.subplots(figsize=(14, 9))
        ax_text.axis('off')

        observation_text = "Observações:\n\n" + self.txt_observation.toPlainText() + "\n\n"
        stats_text = "Estatísticas:\n\n" + self.text_stats.toPlainText()
        full_text = observation_text + stats_text

        lines = stats_text.split('\n')
        mid_index = len(lines) // 2
        left_column = '\n'.join(lines[:mid_index])
        right_column = '\n'.join(lines[mid_index:])
        
        ax_text.text(0.1, 0.9, "Observações:", fontsize=12, fontweight='bold', va='top')
        ax_text.text(0.1, 0.8, observation_text, fontsize=10, va='top', wrap=True)
        ax_text.text(0.1, 0.5, "Estatísticas:", fontsize=12, fontweight='bold', va='top')
        ax_text.text(0.1, 0.4, left_column, fontsize=10, va='top')
        ax_text.text(0.55, 0.4, right_column, fontsize=10, va='top')
        
        pdf.savefig(fig_text, bbox_inches='tight')
        plt.close(fig_text)

        # Gráfico de comparação, se existir
        if hasattr(self, 'fig_comparison') and self.fig_comparison is not None:
            pdf.savefig(self.fig_comparison, bbox_inches='tight')
            print("Gráficos de comparação salvos no PDF.")

        # Salvando todos os gráficos adicionados no tab widget
        for i in range(self.plots_tab_widget.count()):
            tab_name = self.plots_tab_widget.tabText(i)
            canvas = self.plots_tab_widget.widget(i)
            if hasattr(canvas, 'figure'):
                fig = canvas.figure
                pdf.savefig(fig, bbox_inches='tight')
                print(f"Gráfico '{tab_name}' salvo no PDF.")

        # Adiciona o gráfico personalizado, se existir, ao final do PDF
        if hasattr(self, 'fig_custom') and self.fig_custom is not None:
            pdf.savefig(self.fig_custom, bbox_inches='tight')
            print("Gráfico personalizado salvo no PDF.")

    QMessageBox.information(self, "Sucesso", f"PDF salvo em: {save_path}")
