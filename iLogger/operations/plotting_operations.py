import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import concurrent.futures
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication

def plot_graphs(self):
    clear_plots(self)
    total_files = self.list_files.count()
    if total_files > 0:
        furos_do_disco_de_freio = int(self.txt_furos.text() or 12)

        self.fig_rot = plt.figure(figsize=(14, 9), dpi=100)
        self.fig_vel = plt.figure(figsize=(14, 9), dpi=100)
        self.fig_rel = plt.figure(figsize=(14, 9), dpi=100)
        self.fig_acc = plt.figure(figsize=(14, 9), dpi=100)
        self.fig_decel = plt.figure(figsize=(14, 9), dpi=100)
        self.fig_dist = plt.figure(figsize=(14, 9), dpi=100)

        ax_rot = self.fig_rot.add_subplot(111)
        ax_vel = self.fig_vel.add_subplot(111)
        ax_rel = self.fig_rel.add_subplot(111)
        ax_acc = self.fig_acc.add_subplot(111)
        ax_decel = self.fig_decel.add_subplot(111)
        ax_dist = self.fig_dist.add_subplot(111)

        stats_text = "Estatísticas de Cada Arquivo:\n\n"
        self.all_stats = []

        def read_and_validate_csv(file_path):
            try:
                df = pd.read_csv(file_path)
                if 'f1' not in df.columns or 'f2' not in df.columns:
                    return None, f"Arquivo {file_path} inválido: colunas 'f1' ou 'f2' ausentes."
                return df, None
            except Exception as e:
                return None, f"Erro ao ler {file_path}: {str(e)}"

        file_paths = [self.list_files.item(i).text() for i in range(total_files)]
        results = []
        errors = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_file = {executor.submit(read_and_validate_csv, fp): fp for fp in file_paths}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                fp = future_to_file[future]
                df, error = future.result()
                if error:
                    errors.append(error)
                else:
                    results.append((fp, df))
                QApplication.processEvents()

        if errors:
            QMessageBox.warning(self, "Aviso", "\n".join(errors))

        for idx, (file_path, df) in enumerate(results):
            file_name = os.path.basename(file_path)
            try:
                tabela1 = df.set_index('f1')
                tabela2 = df.set_index('f2')
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao processar {file_name}: {str(e)}")
                continue

            f1 = tabela1.index.values
            f2 = tabela2.index.values

            rot_bruto = []
            vel_bruto = []
            for j in range(int(len(f1) / 10)):
                rot_bruto.append(sum(f2[j * 10:j * 10 + 10]))
                vel_bruto.append(sum(f1[j * 10:j * 10 + 10]))

            rot = [k * 20 * 60 for k in rot_bruto]
            vel_kmh = [l * 2 * 0.29 * 3.1415 * 20 * 3.6 / furos_do_disco_de_freio for l in vel_bruto]
            vel_ms = [v * (5 / 18) for v in vel_kmh]
            t = np.linspace(0, 0.05 * len(f1) / 10, int(len(f1) / 10))

            b, a = signal.butter(4, 0.05, analog=False)
            sig_rot = signal.filtfilt(b, a, rot)
            sig_vel_ms = signal.filtfilt(b, a, vel_ms)

            dt = np.diff(t)
            acc = np.diff(sig_vel_ms) / dt
            t_acc = t[:-1]

            sig_acc = signal.filtfilt(b, a, acc)
            decel = -acc
            sig_decel = signal.filtfilt(b, a, decel)

            distancia = np.cumsum(sig_vel_ms * np.diff(t, append=t[-1] + dt[-1]))

            ax_rot.plot(t, rot, color='silver', alpha=0.5, label=f'Original RPM {idx+1}')
            ax_rot.plot(t, sig_rot, label=f'Filtered RPM {idx+1}')

            ax_vel.plot(t, vel_kmh, color='silver', alpha=0.5, label=f'Original {idx+1}')
            ax_vel.plot(t, [v * (18 / 5) for v in sig_vel_ms], label=f'Filtered {idx+1}')

            ax_acc.plot(t_acc, acc, color='silver', alpha=0.5, label=f'Original {idx+1}')
            ax_acc.plot(t_acc, sig_acc, label=f'Filtered {idx+1}')

            ax_decel.plot(t_acc, decel, color='silver', alpha=0.5, label=f'Original {idx+1}')
            ax_decel.plot(t_acc, sig_decel, label=f'Filtered {idx+1}')

            ax_dist.plot(t, distancia, label=f'Distância Percorrida {idx+1}')

            plot_relation(self, sig_rot, [v * (18 / 5) for v in sig_vel_ms], ax_rel, idx, file_name)

            max_vel = max(sig_vel_ms) * (18 / 5)
            max_rpm = max(sig_rot)
            avg_vel = np.mean(sig_vel_ms) * (18 / 5)
            avg_rpm = np.mean(sig_rot)
            max_acc = max(sig_acc)
            avg_acc = np.mean(sig_acc)
            max_decel = max(sig_decel)
            avg_decel = np.mean(sig_decel)
            distancia_total = distancia[-1]

            stats = {
                'file': file_name,
                'max_vel': max_vel,
                'max_rpm': max_rpm,
                'avg_vel': avg_vel,
                'avg_rpm': avg_rpm,
                'max_acc': max_acc,
                'avg_acc': avg_acc,
                'max_decel': max_decel,
                'avg_decel': avg_decel,
                'distancia_total': distancia_total
            }
            self.all_stats.append(stats)

            stats_text += f"Arquivo {idx+1} ({stats['file']}):\n"
            stats_text += f"  - Velocidade Máxima: {max_vel:.2f} Km/h\n"
            stats_text += f"  - RPM Máximo: {max_rpm:.2f} RPM\n"
            stats_text += f"  - Velocidade Média: {avg_vel:.2f} Km/h\n"
            stats_text += f"  - RPM Médio: {avg_rpm:.2f} RPM\n"
            stats_text += f"  - Aceleração Máxima: {max_acc:.2f} m/s²\n"
            stats_text += f"  - Aceleração Média: {avg_acc:.2f} m/s²\n"
            stats_text += f"  - Desaceleração Máxima: {max_decel:.2f} m/s²\n"
            stats_text += f"  - Desaceleração Média: {avg_decel:.2f} m/s²\n"
            stats_text += f"  - Distância Total: {distancia_total:.2f} m\n\n"

        if len(self.all_stats) > 1:
            first_file_stats = self.all_stats[0]
            stats_text += "\nVariações em Relação ao Primeiro Arquivo:\n\n"
            for i in range(1, len(self.all_stats)):
                stats = self.all_stats[i]
                vel_diff = stats['max_vel'] - first_file_stats['max_vel']
                if vel_diff >= 0:
                    stats_text += f"Arquivo {i+1} ({stats['file']}):\n  - Aumento de Velocidade Máxima: {vel_diff:.2f} Km/h\n"
                else:
                    stats_text += f"Arquivo {i+1} ({stats['file']}):\n  - Redução de Velocidade Máxima: {abs(vel_diff):.2f} Km/h\n"

                rpm_diff = stats['max_rpm'] - first_file_stats['max_rpm']
                if rpm_diff >= 0:
                    stats_text += f"  - Aumento de RPM Máximo: {rpm_diff:.2f} RPM\n"
                else:
                    stats_text += f"  - Redução de RPM Máximo: {abs(rpm_diff):.2f} RPM\n"

                avg_vel_diff = (stats['avg_vel'] - first_file_stats['avg_vel']) / first_file_stats['avg_vel'] * 100
                if avg_vel_diff >= 0:
                    stats_text += f"  - Aumento de Velocidade Média: {avg_vel_diff:.2f}%\n"
                else:
                    stats_text += f"  - Redução de Velocidade Média: {abs(avg_vel_diff):.2f}%\n"

                avg_rpm_diff = (stats['avg_rpm'] - first_file_stats['avg_rpm']) / first_file_stats['avg_rpm'] * 100
                if avg_rpm_diff >= 0:
                    stats_text += f"  - Aumento de RPM Médio: {avg_rpm_diff:.2f}%\n"
                else:
                    stats_text += f"  - Redução de RPM Médio: {abs(avg_rpm_diff):.2f}%\n"

                acc_diff = stats['max_acc'] - first_file_stats['max_acc']
                if acc_diff >= 0:
                    stats_text += f"  - Aumento de Aceleração Máxima: {acc_diff:.2f} m/s²\n"
                else:
                    stats_text += f"  - Redução de Aceleração Máxima: {abs(acc_diff):.2f} m/s²\n"

                avg_acc_diff = (stats['avg_acc'] - first_file_stats['avg_acc']) / first_file_stats['avg_acc'] * 100
                if avg_acc_diff >= 0:
                    stats_text += f"  - Aumento de Aceleração Média: {avg_acc_diff:.2f}%\n"
                else:
                    stats_text += f"  - Redução de Aceleração Média: {abs(avg_acc_diff):.2f}%\n"

                decel_diff = stats['max_decel'] - first_file_stats['max_decel']
                if decel_diff >= 0:
                    stats_text += f"  - Aumento de Desaceleração Máxima: {decel_diff:.2f} m/s²\n"
                else:
                    stats_text += f"  - Redução de Desaceleração Máxima: {abs(decel_diff):.2f} m/s²\n"

                avg_decel_diff = (stats['avg_decel'] - first_file_stats['avg_decel']) / first_file_stats['avg_decel'] * 100
                if avg_decel_diff >= 0:
                    stats_text += f"  - Aumento de Desaceleração Média: {avg_decel_diff:.2f}%\n"
                else:
                    stats_text += f"  - Redução de Desaceleração Média: {abs(avg_decel_diff):.2f}%\n"

                distancia_diff = stats['distancia_total'] - first_file_stats['distancia_total']
                if distancia_diff >= 0:
                    stats_text += f"  - Aumento de Distância Total: {distancia_diff:.2f} m\n"
                else:
                    stats_text += f"  - Redução de Distância Total: {abs(distancia_diff):.2f} m\n\n"

        ax_rot.set_xlabel('Tempo (s)')
        ax_rot.set_ylabel('RPM')
        ax_rot.set_title("Rotação do Motor (RPM)", fontsize=14, pad=10)
        ax_rot.legend(loc='upper right')
        ax_rot.grid(True)

        ax_vel.set_xlabel('Tempo (s)')
        ax_vel.set_ylabel('Km/h')
        ax_vel.set_title("Velocidade", fontsize=14, pad=10)
        ax_vel.legend(loc='upper right')
        ax_vel.grid(True)

        ax_rel.set_xlabel('Velocidade (Km/h)')
        ax_rel.set_ylabel('RPM')
        ax_rel.set_title("RPM vs Velocidade - Curva CVT", fontsize=14, pad=10)
        ax_rel.legend(loc='upper right')
        ax_rel.grid(True)

        ax_acc.set_xlabel('Tempo (s)')
        ax_acc.set_ylabel('Aceleração (m/s²)')
        ax_acc.set_title("Aceleração", fontsize=14, pad=10)
        ax_acc.legend(loc='upper right')
        ax_acc.grid(True)

        ax_decel.set_xlabel('Tempo (s)')
        ax_decel.set_ylabel('Desaceleração (m/s²)')
        ax_decel.set_title("Desaceleração", fontsize=14, pad=10)
        ax_decel.legend(loc='upper right')
        ax_decel.grid(True)

        ax_dist.set_xlabel('Tempo (s)')
        ax_dist.set_ylabel('Distância (m)')
        ax_dist.set_title("Distância Percorrida", fontsize=14, pad=10)
        ax_dist.legend(loc='upper right')
        ax_dist.grid(True)

        self.plots_tab_widget.addTab(FigureCanvas(self.fig_rot), "Rotação do Motor")
        self.plots_tab_widget.addTab(FigureCanvas(self.fig_vel), "Velocidade")
        self.plots_tab_widget.addTab(FigureCanvas(self.fig_rel), "Relação RPM x Speed")
        self.plots_tab_widget.addTab(FigureCanvas(self.fig_acc), "Aceleração")
        self.plots_tab_widget.addTab(FigureCanvas(self.fig_decel), "Desaceleração")
        self.plots_tab_widget.addTab(FigureCanvas(self.fig_dist), "Distância Percorrida")

        self.text_stats.setText(stats_text)
        plot_comparison_graphs(self, self.all_stats)
        add_statistics_to_plots(self, self.all_stats)

        self.axis_data = {
            "Tempo (s)": t,
            "RPM": sig_rot,
            "Velocidade (Km/h)": [v * (18 / 5) for v in sig_vel_ms],
            "Aceleração (m/s²)": sig_acc,
            "Desaceleração (m/s²)": sig_decel,
            "Distância (m)": distancia
        }

        update_axis_comboboxes(self)

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

        plot_metrics_table(self, stats_df)
    else:
        QMessageBox.critical(self, "Erro", "Nenhum arquivo selecionado.")

def update_axis_comboboxes(self):
    self.combo_x.clear()
    self.combo_y.clear()
    self.combo_z.clear()

    axes = list(self.axis_data.keys())
    self.combo_x.addItems(axes)
    self.combo_y.addItems(axes)
    self.combo_z.addItems([""] + axes)

    self.combo_x.setCurrentText("Tempo (s)")
    self.combo_y.setCurrentText("Velocidade (Km/h)")
    self.combo_z.setCurrentText("")

def update_custom_plot(self):
    self.fig_custom.clear()

    # Lê quais colunas/variáveis o usuário selecionou
    x_axis = self.combo_x.currentText()
    y_axis = self.combo_y.currentText()
    z_axis = self.combo_z.currentText()  # Terceiro combo para segundo eixo Y

    if not x_axis or not y_axis:
        QMessageBox.warning(self, "Erro", "Selecione pelo menos os eixos X e Y.")
        return

    # Busca os dados que foram armazenados em self.axis_data
    x_data = self.axis_data.get(x_axis)
    y_data = self.axis_data.get(y_axis)
    z_data = self.axis_data.get(z_axis) if z_axis else None  # Pode estar vazio

    # Verifica se de fato temos dados para X e Y
    if x_data is None or y_data is None:
        QMessageBox.warning(self, "Erro", "Dados para os eixos X ou Y não encontrados.")
        return

    # Se precisar interpolar tamanhos diferentes (opcional):
    min_len = min(len(x_data), len(y_data), len(z_data) if z_data is not None else len(x_data))
    x_data = x_data[:min_len]
    y_data = y_data[:min_len]
    if z_data is not None:
        z_data = z_data[:min_len]

    # Cria o subplot
    ax1 = self.fig_custom.add_subplot(111)

    # Primeiro eixo Y (em azul, por exemplo)
    ax1.plot(x_data, y_data, color="blue", label=y_axis)
    ax1.set_xlabel(x_axis)
    ax1.set_ylabel(y_axis, color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Se houver z_axis selecionado, cria o segundo eixo Y (twinx)
    if z_data is not None and z_axis != "":
        ax2 = ax1.twinx()
        ax2.plot(x_data, z_data, color="red", label=z_axis)
        ax2.set_ylabel(z_axis, color="red")
        ax2.tick_params(axis="y", labelcolor="red")

        # Combina legendas dos dois eixos
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="best")
        title = f"{y_axis} e {z_axis} x {x_axis}"
    else:
        # Se não tiver z_axis, legenda fica só no ax1
        ax1.legend(loc="best")
        title = f"{y_axis} x {x_axis}"

    # Título, grade e atualização do canvas com os eixos escolhidos
    ax1.set_title(title)
    ax1.grid(True)
    self.canvas_custom.draw()

def save_custom_plot_image(self):
    if not hasattr(self, 'fig_custom') or self.fig_custom is None:
        QMessageBox.warning(self, "Erro", "Nenhum gráfico personalizado para salvar.")
        return

    file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Imagem", "", "PNG files (*.png);;JPEG files (*.jpg)")
    if file_path:
        self.fig_custom.savefig(file_path, dpi=300, bbox_inches='tight')
        QMessageBox.information(self, "Sucesso", f"Imagem salva em: {file_path}")

def plot_relation(self, sig_rot, sig_vel, ax_rel, i, file_name):
    raio_pneu = 0.29
    pi = 3.1415
    #circunferencia_pneu = 2 * pi * raio_pneu
    #reducao_fixa = 9.5
    #ow_ratio = 4.0
    #high_ratio = 0.9

    #velocidade_low_ratio = np.linspace(0, 12, 200)
    #rpm_low_ratio = ((velocidade_low_ratio * low_ratio * reducao_fixa) / circunferencia_pneu) * (1000 / 60)
    #velocidade_high_ratio = np.linspace(0, 52, 200)
    #rpm_high_ratio = ((velocidade_high_ratio * high_ratio * reducao_fixa) / circunferencia_pneu) * (1000 / 60)
    #velocidade_faixa = np.linspace(12, 52, 200)
    #rpm_limite = np.linspace(4100, 4100, 200)

    ax_rel.plot(sig_vel, sig_rot, marker='o', linestyle='--', label=file_name)
    #ax_rel.plot(velocidade_low_ratio, rpm_low_ratio, color='green', linestyle='-')
    #ax_rel.plot(velocidade_high_ratio, rpm_high_ratio, color='orange', linestyle='-')
    #ax_rel.plot(velocidade_faixa, rpm_limite, color='red', linestyle='--')

    ax_rel.set_xlabel('Velocidade (Km/h)')
    ax_rel.set_ylabel('RPM')
    ax_rel.set_title("RPM vs Velocidade - Curva CVT", fontsize=14, pad=10)
    ax_rel.grid(True)
    ax_rel.legend(loc='upper right')

def add_statistics_to_plots(self, all_stats):
    if len(all_stats) > 1:
        first_file_stats = all_stats[0]

        ax_rot = self.fig_rot.axes[0]
        stats_text_rot = "Variações em Relação ao Primeiro Arquivo:\n"
        for i in range(1, len(all_stats)):
            stats = all_stats[i]
            avg_rpm_diff = (stats['avg_rpm'] - first_file_stats['avg_rpm']) / first_file_stats['avg_rpm'] * 100
            stats_text_rot += f"Arquivo {i+1}:\n  - Variação RPM Médio: {avg_rpm_diff:.2f}%\n"
        ax_rot.text(0.98, 0.02, stats_text_rot, transform=ax_rot.transAxes, fontsize=10, color='blue',
                    verticalalignment='bottom', horizontalalignment='right', bbox=dict(facecolor='white', alpha=0.8))

        ax_vel = self.fig_vel.axes[0]
        stats_text_vel = "Variações em Relação ao Primeiro Arquivo:\n"
        for i in range(1, len(all_stats)):
            stats = all_stats[i]
            avg_vel_diff = (stats['avg_vel'] - first_file_stats['avg_vel']) / first_file_stats['avg_vel'] * 100
            stats_text_vel += f"Arquivo {i+1}:\n  - Variação Velocidade Média: {avg_vel_diff:.2f}%\n"
        ax_vel.text(0.98, 0.02, stats_text_vel, transform=ax_vel.transAxes, fontsize=10, color='blue',
                    verticalalignment='bottom', horizontalalignment='right', bbox=dict(facecolor='white', alpha=0.8))

        ax_rel = self.fig_rel.axes[0]
        stats_text_rel = "Variações em Relação ao Primeiro Arquivo:\n"
        for i in range(1, len(all_stats)):
            stats = all_stats[i]
            avg_rpm_diff = (stats['avg_rpm'] - first_file_stats['avg_rpm']) / first_file_stats['avg_rpm'] * 100
            avg_vel_diff = (stats['avg_vel'] - first_file_stats['avg_vel']) / first_file_stats['avg_vel'] * 100
            stats_text_rel += f"Arquivo {i+1}:\n  - Variação RPM Médio: {avg_rpm_diff:.2f}%\n  - Variação Velocidade Média: {avg_vel_diff:.2f}%\n"
        ax_rel.text(0.98, 0.02, stats_text_rel, transform=ax_rel.transAxes, fontsize=10, color='blue',
                    verticalalignment='bottom', horizontalalignment='right', bbox=dict(facecolor='white', alpha=0.8))

        ax_acc = self.fig_acc.axes[0]
        stats_text_acc = "Variações em Relação ao Primeiro Arquivo:\n"
        for i in range(1, len(all_stats)):
            stats = all_stats[i]
            avg_acc_diff = (stats['avg_acc'] - first_file_stats['avg_acc']) / first_file_stats['avg_acc'] * 100
            stats_text_acc += f"Arquivo {i+1}:\n  - Variação Aceleração Média: {avg_acc_diff:.2f}%\n"
        ax_acc.text(0.98, 0.02, stats_text_acc, transform=ax_acc.transAxes, fontsize=10, color='blue',
                    verticalalignment='bottom', horizontalalignment='right', bbox=dict(facecolor='white', alpha=0.8))

        ax_decel = self.fig_decel.axes[0]
        stats_text_decel = "Variações em Relação ao Primeiro Arquivo:\n"
        for i in range(1, len(all_stats)):
            stats = all_stats[i]
            avg_decel_diff = (stats['avg_decel'] - first_file_stats['avg_decel']) / first_file_stats['avg_decel'] * 100
            stats_text_decel += f"Arquivo {i+1}:\n  - Variação Desaceleração Média: {avg_decel_diff:.2f}%\n"
        ax_decel.text(0.98, 0.02, stats_text_decel, transform=ax_decel.transAxes, fontsize=10, color='blue',
                    verticalalignment='bottom', horizontalalignment='right', bbox=dict(facecolor='white', alpha=0.8))

def plot_comparison_graphs(self, all_stats):
    self.fig_comparison.set_size_inches(10, 8)
    self.fig_comparison.clear()

    ax1 = self.fig_comparison.add_subplot(221)
    ax2 = self.fig_comparison.add_subplot(222)
    ax3 = self.fig_comparison.add_subplot(223)
    ax4 = self.fig_comparison.add_subplot(224)

    files = [stats['file'] for stats in all_stats]
    max_vel = [stats['max_vel'] for stats in all_stats]
    max_rpm = [stats['max_rpm'] for stats in all_stats]
    avg_vel = [stats['avg_vel'] for stats in all_stats]
    avg_rpm = [stats['avg_rpm'] for stats in all_stats]
    max_acc = [stats['max_acc'] for stats in all_stats]
    avg_acc = [stats['avg_acc'] for stats in all_stats]
    max_decel = [stats['max_decel'] for stats in all_stats]
    avg_decel = [stats['avg_decel'] for stats in all_stats]

    plot_bar_with_values(ax1, files, max_vel, "Velocidade Máxima (Km/h)", "Km/h", 'blue')
    plot_bar_with_values(ax2, files, max_rpm, "RPM Máximo", "RPM", 'green')
    plot_bar_with_values(ax3, files, avg_vel, "Velocidade Média (Km/h)", "Km/h", 'orange')
    plot_bar_with_values(ax4, files, avg_rpm, "RPM Médio", "RPM", 'red')

    self.fig_comparison.tight_layout(pad=2, w_pad=2, h_pad=2)
    self.canvas_comparison.draw()

def plot_bar_with_values(ax, x, y, title, ylabel, color):
    bars = ax.bar(x, y, color=color)
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.tick_params(axis='x', rotation=0)
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height / 2),
                        ha='center', va='center', color='white', fontsize=10)
        else:
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)

def plot_metrics_table(self, stats_df):
    self.fig_metrics_table = plt.figure(figsize=(14, 9))
    ax = self.fig_metrics_table.add_subplot(111)
    ax.axis('off')

    stats_df.columns = [
        'Vel. Máx (Km/h)',
        'RPM Máx',
        'Vel. Média (Km/h)',
        'RPM Médio',
        'Acel. Máx (m/s²)',
        'Acel. Média (m/s²)',
        'Desac. Máx (m/s²)',
        'Desac. Média (m/s²)',
        'Distância Total (m)'
    ]

    table_metrics = ax.table(
        cellText=stats_df.values,
        colLabels=stats_df.columns,
        rowLabels=stats_df.index,
        loc='center',
        cellLoc='center',
        bbox=[0.05, 0.65, 0.95, 0.3]
    )

    table_metrics.auto_set_font_size(False)
    table_metrics.set_fontsize(10)
    table_metrics.scale(1.2, 1.2)

    ax.text(0.5, 0.98, "Tabela de Métricas", fontsize=14, ha='center', va='top')

    if len(stats_df) > 1:
        first_file_stats = stats_df.iloc[0]
        variations = []

        for i in range(1, len(stats_df)):
            file_stats = stats_df.iloc[i]
            variation = {
                'Arquivo': stats_df.index[i],
                'Variação Vel. Máx (%)': ((file_stats['Vel. Máx (Km/h)'] - first_file_stats['Vel. Máx (Km/h)']) / first_file_stats['Vel. Máx (Km/h)']) * 100,
                'Variação RPM Máx (%)': ((file_stats['RPM Máx'] - first_file_stats['RPM Máx']) / first_file_stats['RPM Máx']) * 100,
                'Variação Vel. Média (%)': ((file_stats['Vel. Média (Km/h)'] - first_file_stats['Vel. Média (Km/h)']) / first_file_stats['Vel. Média (Km/h)']) * 100,
                'Variação RPM Médio (%)': ((file_stats['RPM Médio'] - first_file_stats['RPM Médio']) / first_file_stats['RPM Médio']) * 100,
                'Variação Acel. Máx (%)': ((file_stats['Acel. Máx (m/s²)'] - first_file_stats['Acel. Máx (m/s²)']) / first_file_stats['Acel. Máx (m/s²)']) * 100,
                'Variação Acel. Média (%)': ((file_stats['Acel. Média (m/s²)'] - first_file_stats['Acel. Média (m/s²)']) / first_file_stats['Acel. Média (m/s²)']) * 100,
                'Variação Desac. Máx (%)': ((file_stats['Desac. Máx (m/s²)'] - first_file_stats['Desac. Máx (m/s²)']) / first_file_stats['Desac. Máx (m/s²)']) * 100,
                'Variação Desac. Média (%)': ((file_stats['Desac. Média (m/s²)'] - first_file_stats['Desac. Média (m/s²)']) / first_file_stats['Desac. Média (m/s²)']) * 100,
                'Variação Distância Total (%)': ((file_stats['Distância Total (m)'] - first_file_stats['Distância Total (m)']) / first_file_stats['Distância Total (m)']) * 100
            }
            variations.append(variation)

        variations_df = pd.DataFrame(variations)
        variations_df.set_index('Arquivo', inplace=True)
        variations_df = variations_df.round(2)

        table_variations = ax.table(
            cellText=variations_df.values,
            colLabels=variations_df.columns,
            rowLabels=variations_df.index,
            loc='center',
            cellLoc='center',
            bbox=[0.05, 0.25, 0.95, 0.35]
        )

        table_variations.auto_set_font_size(False)
        table_variations.set_fontsize(10)
        table_variations.scale(1.2, 1.2)

        ax.text(0.5, 0.23, "Variações Estatísticas em Relação ao Primeiro Arquivo", fontsize=14, ha='center', va='bottom')

def clear_plots(self):
    for fig in [self.fig_rot, self.fig_vel, self.fig_rel, self.fig_acc, self.fig_decel, self.fig_dist, self.fig_comparison, self.fig_custom, self.fig_metrics_table]:
        if fig is not None:
            plt.close(fig)
    self.plots_tab_widget.clear()
    self.text_stats.clear()
    self.plots_tab_widget.addTab(self.stats_widget, "Estatísticas e Comparação")
    self.plots_tab_widget.addTab(self.custom_plot_widget, "Gráfico Personalizado")
