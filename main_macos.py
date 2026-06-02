# solar_ui.py
import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QFrame, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox, QHeaderView, QDialog, QDateEdit, QTimeEdit,
    QComboBox, QDoubleSpinBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QSize, QDate, QTime 
from PyQt5.QtGui import QFont, QPixmap, QIcon
import sqlite3
import pandas as pd
import math
import webbrowser
from datetime import datetime, date, time, timedelta

SIDEBAR_COLOR = "#0F395E"
SIDEBAR_WIDTH_RATIO = 0.33  # 33% of window width
LEFT_WIDTH = 40
RIGHT_WIDTH = 60


def round_up_to_interval(dt, interval_minutes):
    minutes_to_add = (interval_minutes - dt.minute % interval_minutes) % interval_minutes

    if minutes_to_add == 0 and dt.second == 0:
        return dt.replace(second=0, microsecond=0)

    return (dt + timedelta(minutes=minutes_to_add)).replace(second=0, microsecond=0)


def round_down_to_interval(dt, interval_minutes):
    return (dt - timedelta(
        minutes=dt.minute % interval_minutes,
        seconds=dt.second,
        microseconds=dt.microsecond
    )).replace(second=0, microsecond=0)


def calculate_sunrise_sunset(current_date, latitude_deg):
    n = current_date.timetuple().tm_yday

    delta = 23.45 * math.sin(
        math.radians((360 / 365.24) * (284 + n))
    )

    phi = math.radians(latitude_deg)
    delta_rad = math.radians(delta)

    cos_ws = -math.tan(phi) * math.tan(delta_rad)
    cos_ws = max(-1, min(1, cos_ws))
    ws = math.degrees(math.acos(cos_ws))

    hsr = 12 - ws / 15
    hss = 12 + ws / 15

    sunrise = datetime.combine(current_date, time()) + timedelta(hours=hsr)
    sunset  = datetime.combine(current_date, time()) + timedelta(hours=hss)

    return sunrise, sunset


def generate_expected_intervals(start_date, end_date, latitude, interval_minutes, custom_start_time=None, custom_end_time=None):
    expected_times = []

    current_day = start_date
    final_day = end_date

    while current_day <= final_day:
        sunrise, sunset = calculate_sunrise_sunset(current_day, latitude)

        sunrise = round_up_to_interval(sunrise, interval_minutes)
        sunset = round_down_to_interval(sunset, interval_minutes)

        # Only apply custom start time to the first day
        if custom_start_time and current_day == start_date:
            sunrise = datetime.combine(current_day, custom_start_time)

        # Only apply custom end time to the last day
        if custom_end_time and current_day == end_date:
            sunset = datetime.combine(current_day, custom_end_time)

        current_time = sunrise

        while current_time <= sunset:
            expected_times.append(current_time)
            current_time += timedelta(minutes=interval_minutes)

        current_day += timedelta(days=1)

    return expected_times

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # quando está empacotado pelo PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SidebarButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(60)
        self.setFont(QFont("sans-serif", 18))
        # Styles: white text, 1px white border, rounded corners
        self.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background: transparent;
                border: 1px solid white;
                border-radius: 30px;
                padding: 8px 14px;
                margin-left: 20px;
                margin-right: 20px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.08);
            }}
            QPushButton:pressed {{
                background: rgba(255,255,255,0.12);
            }}
        """)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Sobre o Solarímetro")
        self.setWindowIcon(QIcon(resource_path("images/solarimetro_icon.icns")))
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }

            QLabel {
                color: black;
            }
        """)
        self.setFixedSize(420, 490)

        layout = QVBoxLayout(self)

        # More padding
        layout.setContentsMargins(40, 30, 40, 40)

        # Center everything
        layout.setAlignment(Qt.AlignCenter)

        # Better spacing between widgets
        layout.setSpacing(18)

        icon_label = QLabel()
        icon_pixmap = QPixmap(resource_path("images/solarimetro_icon.png"))

        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(
                    140,
                    140,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        icon_label.setAlignment(Qt.AlignCenter)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 1)
        shadow.setColor(Qt.black)

        icon_label.setGraphicsEffect(shadow)

        title = QLabel("Solarímetro")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("sans-serif", 24, weight=QFont.Bold))

        version = QLabel("Versão 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setFont(QFont("sans-serif", 12))

        author_label = QLabel("Desenvolvido por Efrain Artola")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setFont(QFont("sans-serif", 12))

        license_label = QLabel("Licença: Uso acadêmico e institucional")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setFont(QFont("sans-serif", 12))

        acknowledgements = QLabel(
            "Agradecimentos:\n"
            "UNASP, NUTEA e colaboradores do projeto.\n\n"
            "Agradecimento especial ao Prof. Ítalo Alberto Gatica Ríspoli,\n"
            "Dr. em Ciências da Engenharia,\n"
            "pelo apoio e orientação no desenvolvimento do projeto."
        )
        acknowledgements.setAlignment(Qt.AlignCenter)
        acknowledgements.setWordWrap(True)
        acknowledgements.setFont(QFont("sans-serif", 12))

        copyright_label = QLabel(
            "© 2026 Solarímetro. Todos os direitos reservados."
        )
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont("sans-serif", 11))

        layout.addStretch()

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(author_label)
        layout.addWidget(license_label)
        layout.addWidget(acknowledgements)

        layout.addSpacing(10)

        layout.addWidget(copyright_label)

        layout.addStretch()


class StartWindow(QWidget):
    def __init__(self, switch_to_main_callback, controller):
        super().__init__()
        self.switch_to_main_callback = switch_to_main_callback
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Solarímetro")
        self.setWindowIcon(QIcon(resource_path("images/solarimetro_icon.icns")))
        # Root layout
        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0)

        # Sidebar container
        sidebar = QFrame()
        sidebar.setStyleSheet(f"background: {SIDEBAR_COLOR};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(26)

        # Buttons
        btn_create = SidebarButton("Criar banco de dados")
        btn_create.clicked.connect(self.on_create_db)
        btn_open = SidebarButton("Abrir base de dados")
        btn_credits = SidebarButton("Créditos")
        btn_help = SidebarButton("Ajuda")

        # Hook up open -> switch to main app window
        btn_open.clicked.connect(self.on_open_db)
        btn_credits.clicked.connect(self.show_about_dialog)
        btn_help.clicked.connect(self.open_help_pdf)

        # Add stretch to push buttons a bit downward and center vertically
        sidebar_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        sidebar_layout.addWidget(btn_create)
        sidebar_layout.addWidget(btn_open)
        sidebar_layout.addWidget(btn_credits)
        sidebar_layout.addWidget(btn_help)
        sidebar_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Right area
        right_area = QFrame()
        right_area.setStyleSheet("""
            QFrame {
                background: white;
            }

            QLabel {
                color: black;
            }
        """)
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(40, 90, 40, 20)
        right_layout.setAlignment(Qt.AlignTop)

        # Unasp Logo
        unasp_logo = QLabel()
        unasp_logo_pixmap = QPixmap(resource_path("images/unasp_logo.png"))

        if not unasp_logo_pixmap.isNull():
            unasp_logo.setPixmap(unasp_logo_pixmap.scaledToWidth(250, Qt.SmoothTransformation))
        else:
            unasp_logo.setText("UNASP")
            unasp_logo.setStyleSheet("color: black; font-size: 24px; font-weight: bold;")
            
        right_layout.addWidget(unasp_logo)

        # Text in right area
        text_1 = QLabel("\nBem-vindo ao Banco De Dados Da Claridade Atmosférica, Irradiância e Irradiação Solar!")
        text_1.setWordWrap(True)
        text_1.setFont(QFont("sans-serif", 21, weight=QFont.Bold))
        right_layout.addWidget(text_1)
        text_1.setContentsMargins(0, 40, 0, 0)

        text_2 = QLabel("\nNUTEA - Núcleo de tecnologia de Engenharia e Arquitetura\nLocalização: UNASP campus Engenheiro Coelho -SP")
        text_2.setWordWrap(True)
        text_2.setFont(QFont("sans-serif", 16))
        right_layout.addWidget(text_2)
        
        # text_3 = QLabel("\nLocalização: UNASP campus Engenheiro Coelho -SP")
        # text_3.setWordWrap(True)
        # text_3.setFont(QFont("sans-serif", 16))
        # right_layout.addWidget(text_3)

        text_4 = QLabel("\nCoordenadas geográficas: Latitude 22° 30’6,12” Sul e Longitude 47°9’59,4” Oeste / Altitude: 682m")
        text_4.setWordWrap(True)
        text_4.setFont(QFont("sans-serif", 16))
        right_layout.addWidget(text_4)

        text_5 = QLabel("\nAbra ou crie um banco de dados para começar!")
        text_5.setWordWrap(True)
        text_5.setFont(QFont("sans-serif", 21, weight=QFont.Bold))
        right_layout.addWidget(text_5)

        # Add to root and divisor orange line
        divider = QFrame()
        divider.setFixedWidth(5)
        divider.setStyleSheet("background-color: #EF5C2A; border: none;")

        root.addWidget(sidebar, stretch=LEFT_WIDTH)
        root.addWidget(divider)
        root.addWidget(right_area, stretch=RIGHT_WIDTH)
        root.setSpacing(0)


        self.setLayout(root)
        self.setFixedSize(900, 600)

    def on_open_db(self):
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir banco de dados",
            "",
            "Banco de Dados SQLite (*.db);;Todos os arquivos (*)"
        )

        if not file_path:
            return  # user cancelled

        # Validate the SQLite database
        try:
            if not os.path.exists(file_path):
                raise ValueError("O arquivo não existe.")

            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()

            # Check if table 'dados_solares' exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dados_solares';")
            table_exists = cursor.fetchone()
            if not table_exists:
                raise ValueError("O banco de dados não contém a tabela esperada 'dados_solares'.")

            # Check columns
            cursor.execute("PRAGMA table_info(dados_solares);")
            columns = [col[1] for col in cursor.fetchall()]
            expected_columns = ["Data-Hora", "Sample Av Pira1[W/m2]", "Sample Av Pira2[W/m2]"]
            if columns != expected_columns:
                raise ValueError("O banco de dados não possui as colunas corretas ou na ordem correta.")

            conn.close()

            # If all is fine, save path and switch to main window
            self.controller.db_path = file_path
            self.switch_to_main_callback()

        except (sqlite3.Error, ValueError) as e:
            QMessageBox.critical(
                self,
                "Banco de Dados Inválido",
                "O arquivo selecionado não é um banco de dados válido."
            )
            print("ERRO TÉCNICO:", e)


    def on_create_db(self):
        # Open dialog for user to choose where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar banco de dados como...",
            "",
            "Banco de Dados SQLite (*.db);;Todos os arquivos (*)"
        )

        if not file_path:
            return  # user cancelled

        # Ensure it ends with .db
        if not file_path.endswith(".db"):
            file_path += ".db"

        try:
            # Create SQLite file
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()

            # Create table with the three columns you specified
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dados_solares (
                    "Data-Hora" TEXT PRIMARY KEY,
                    "Sample Av Pira1[W/m2]" REAL,
                    "Sample Av Pira2[W/m2]" REAL
                );
            """)
            conn.commit()
            conn.close()

            # Show success message
            QMessageBox.information(
                self,
                "Banco de Dados Criado",
                f"O banco de dados foi criado com sucesso em:\n{file_path}"
            )

            self.controller.db_path = file_path
            self.switch_to_main_callback()

        except Exception as e:
            QMessageBox.critical(
            self,
                "Erro",
                f"Ocorreu um erro ao criar o banco de dados:\n{str(e)}"
            )

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()


    def open_help_pdf(self):
        pdf_path = resource_path("docs/manual_solarimetro.pdf")

        if os.path.exists(pdf_path):
            webbrowser.open("file://" + pdf_path)
        else:
            QMessageBox.warning(
                self,
                "Ajuda",
                f"O manual não foi encontrado:\n{pdf_path}"
            )


class SaveChangesDialog(QDialog):
    def __init__(self, file_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salvar Alterações")
        self.setModal(True)
        self.setFixedSize(400, 180)

        self.choice = None  # Armazena a escolha do usuário

        layout = QVBoxLayout(self)

        # Texto principal
        label_text = QLabel(f'Quer salvar as alterações feitas em "{file_name}"?')
        label_text.setWordWrap(True)
        label_text.setFont(QFont("sans-serif", 12))
        layout.addWidget(label_text)

        # Texto informativo
        label_info = QLabel(
            "Alterações manuais e dados importados do Excel serão perdidos se você não salvá-los."
        )
        label_info.setWordWrap(True)
        layout.addWidget(label_info)

        # Layout dos botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Botão Salvar
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setDefault(True)
        btn_salvar.clicked.connect(self.salvar)
        button_layout.addWidget(btn_salvar)

        # Botão Não Salvar
        btn_nao_salvar = QPushButton("Não Salvar")
        btn_nao_salvar.clicked.connect(self.nao_salvar)
        button_layout.addWidget(btn_nao_salvar)

        # Botão Cancelar
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.cancelar)
        button_layout.addWidget(btn_cancelar)

        layout.addLayout(button_layout)

    def salvar(self):
        self.choice = "salvar"
        self.accept()

    def nao_salvar(self):
        self.choice = "nao_salvar"
        self.accept()

    def cancelar(self):
        self.choice = "cancelar"
        self.reject()

class ImportSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações da Importação")
        self.setModal(True)
        self.setFixedSize(420, 280)

        layout = QVBoxLayout(self)

        self.latitude_input = QDoubleSpinBox()
        self.latitude_input.setRange(-90, 90)
        self.latitude_input.setDecimals(6)
        self.latitude_input.setValue(-22.501700)

        self.interval_input = QComboBox()
        self.interval_input.addItems(["1", "2", "5", "10", "15", "30", "60"])
        self.interval_input.setCurrentText("5")

        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())

        layout.addWidget(QLabel("Latitude:"))
        layout.addWidget(self.latitude_input)

        layout.addWidget(QLabel("Intervalo de tempo em minutos:"))
        layout.addWidget(self.interval_input)

        layout.addWidget(QLabel("Data inicial:"))
        layout.addWidget(self.start_date_input)

        layout.addWidget(QLabel("Data final:"))
        layout.addWidget(self.end_date_input)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Continuar")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

    def get_values(self):
        return {
            "latitude": self.latitude_input.value(),
            "interval_minutes": int(self.interval_input.currentText()),
            "start_date": self.start_date_input.date().toPyDate(),
            "end_date": self.end_date_input.date().toPyDate()
        }


class SolarHourDialog(QDialog):
    def __init__(self, first_sunrise, last_sunset, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Horário Solar da Importação")
        self.setModal(True)
        self.setFixedSize(460, 260)

        layout = QVBoxLayout(self)

        info = QLabel(
            f"Horário inicial calculado: {first_sunrise.strftime('%H:%M:%S')}\n"
            f"Horário final calculado: {last_sunset.strftime('%H:%M:%S')}\n\n"
            "Confirme ou ajuste o horário inicial do primeiro dia e o horário final do último dia:"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("HH:mm:ss")
        self.start_time_input.setTime(QTime(first_sunrise.hour, first_sunrise.minute, first_sunrise.second))

        self.end_time_input = QTimeEdit()
        self.end_time_input.setDisplayFormat("HH:mm:ss")
        self.end_time_input.setTime(QTime(last_sunset.hour, last_sunset.minute, last_sunset.second))

        layout.addWidget(QLabel("Hora inicial:"))
        layout.addWidget(self.start_time_input)

        layout.addWidget(QLabel("Hora final:"))
        layout.addWidget(self.end_time_input)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Importar")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

    def get_values(self):
        return {
            "start_time": self.start_time_input.time().toPyTime(),
            "end_time": self.end_time_input.time().toPyTime()
        }


class OverwriteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobrescrever Dados Existentes")
        self.setModal(True)
        self.setFixedSize(460, 180)

        self.choice = None

        layout = QVBoxLayout(self)

        label = QLabel(
            "Se o arquivo Excel tiver datas que já existem no banco de dados, "
            "você deseja sobrescrever esses registros?"
        )
        label.setWordWrap(True)
        label.setFont(QFont("sans-serif", 12))
        layout.addWidget(label)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_overwrite = QPushButton("Sobrescrever")
        btn_no_overwrite = QPushButton("Não Sobrescrever")
        btn_cancel = QPushButton("Cancelar")

        btn_overwrite.clicked.connect(self.overwrite)
        btn_no_overwrite.clicked.connect(self.no_overwrite)
        btn_cancel.clicked.connect(self.cancel)

        buttons.addWidget(btn_overwrite)
        buttons.addWidget(btn_no_overwrite)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def overwrite(self):
        self.choice = "overwrite"
        self.accept()

    def no_overwrite(self):
        self.choice = "no_overwrite"
        self.accept()

    def cancel(self):
        self.choice = "cancel"
        self.reject()


class DailyResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atualizar Resultados Diários")
        self.setModal(True)
        self.setFixedSize(420, 220)

        layout = QVBoxLayout(self)

        self.latitude_input = QDoubleSpinBox()
        self.latitude_input.setRange(-90, 90)
        self.latitude_input.setDecimals(6)
        self.latitude_input.setValue(-22.501700)

        self.interval_input = QComboBox()
        self.interval_input.addItems(["1", "2", "5", "10", "15", "30", "60"])
        self.interval_input.setCurrentText("5")

        layout.addWidget(QLabel("Latitude:"))
        layout.addWidget(self.latitude_input)

        layout.addWidget(QLabel("Intervalo em minutos:"))
        layout.addWidget(self.interval_input)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_update = QPushButton("Atualizar resultados")
        btn_cancel = QPushButton("Cancelar")

        btn_update.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_update)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def get_values(self):
        return {
            "latitude": self.latitude_input.value(),
            "interval_minutes": int(self.interval_input.currentText())
        }


class MainAppWindow(QWidget):
    def __init__(self, return_to_start_callback, db_path=None):
        super().__init__()
        self.return_to_start_callback = return_to_start_callback
        self.db_path = db_path
        self.unsaved_changes = False  # Controle de alterações não salvas
        self.returning_to_start = False
        self.init_ui()

    def mostrar_erro(self, mensagem_usuario, erro=None):
        # Log técnico (para você)
        if erro:
            print("ERRO TÉCNICO:", erro)

        # Mensagem amigável (para o usuário)
        QMessageBox.critical(
            self,
            "Erro",
            mensagem_usuario
        )

    def init_ui(self):
        self.setWindowTitle("Solarímetro")
        self.setWindowIcon(QIcon(resource_path("images/solarimetro_icon.icns")))
        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0)

        # Left sidebar (main app)
        sidebar = QFrame()
        sidebar.setStyleSheet(f"background: {SIDEBAR_COLOR};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(26)

        btn_view_db = SidebarButton("Base de Dados")
        btn_daily = SidebarButton("Resultados Diários")
        btn_monthly = SidebarButton("Resultados Mensais")
        btn_annual = SidebarButton("Resultados Anuais")
        btn_save_close = SidebarButton("Salvar e Sair")

        # Connect buttons to content changes
        btn_view_db.clicked.connect(lambda: self.show_page("view_db"))
        btn_daily.clicked.connect(lambda: self.show_page("daily"))
        btn_monthly.clicked.connect(lambda: self.show_page("monthly"))
        btn_annual.clicked.connect(lambda: self.show_page("annual"))
        btn_save_close.clicked.connect(self.on_save_close)

        # Text Title
        menu_title = QLabel("Menu")
        menu_title.setFont(QFont("sans-serif", 32))
        menu_title.setStyleSheet("color: white;")
        menu_title.setContentsMargins(0, 0, 0, 10)

        sidebar_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        sidebar_layout.addWidget(menu_title, alignment=Qt.AlignHCenter)
        sidebar_layout.addWidget(btn_view_db)
        sidebar_layout.addWidget(btn_daily)
        sidebar_layout.addWidget(btn_monthly)
        sidebar_layout.addWidget(btn_annual)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(btn_save_close)
        sidebar_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Right main area (stacked pages)
        right_area = QFrame()
        right_area.setStyleSheet("background: #f5f5f5;")
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(20, 20, 20, 20)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.build_view_db_page())
        self.pages.addWidget(self.build_daily_page())
        self.pages.addWidget(self.build_monthly_page())
        self.pages.addWidget(self.build_annual_page())

        # Map page names to indexes
        self.page_indexes = {
            "view_db": 0,
            "daily": 1,
            "monthly": 2,
            "annual": 3
        }

        right_layout.addWidget(self.pages)

        divider = QFrame()
        divider.setFixedWidth(5)
        divider.setStyleSheet("background-color: #EF5C2A; border: none;")

        # Add to root layout
        root.addWidget(sidebar, stretch=25)
        root.addWidget(divider)
        root.addWidget(right_area, stretch=75)
        root.setSpacing(0)

        self.setLayout(root)
        screen = QApplication.primaryScreen()
        size = screen.size()
        self.resize(size.width(), size.height())

    def build_view_db_page(self):
        """
        View Database layout:
        - Row 1: Import Excel Data button and Search Data button
        - Row 2: Placeholder table (QTableWidget)
        """
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10,10,10,10)
        container_layout.setSpacing(12)

        # Row 1: action buttons #68C151
        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 12)

        btn_import = QPushButton("Importar dados do Excel")
        btn_import.setMinimumHeight(50)
        btn_import.setFont(QFont("Segoe UI", 16))
        btn_import.setStyleSheet("""
            QPushButton {
                color: #a3a3a3;
                font-weight: 600;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                background: white;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #f2f2f2; }
        """)

        search_input = QLineEdit()
        search_input.setFixedWidth(450)
        search_input.setPlaceholderText(" Insira a data ...")
        search_input.setMinimumHeight(50)
        search_input.setFont(QFont("Segoe UI", 16))
        search_input.setStyleSheet("""
            QLineEdit {
                color: #a3a3a3;
                background: white;                
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLineEdit:hover { background: #f2f2f2; }
        """)

        btn_search = QPushButton("Pesquisar")
        btn_search.setMinimumHeight(50)
        btn_search.setFont(QFont("Segoe UI", 16))
        btn_search.setStyleSheet("""
            QPushButton {
                color: #a3a3a3;
                font-weight: 600;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                background: white;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #f2f2f2; }
        """)

        # Import Excel Data Button Connection
        btn_import.clicked.connect(self.import_excel_data)

        # --- NEW: Connect the search button to the search function ---
        btn_search.clicked.connect(lambda: self.search_in_table(search_input.text()))

        row_top.addWidget(btn_import)
        row_top.addStretch()
        row_top.addWidget(search_input)
        row_top.setSpacing(20)
        row_top.addWidget(btn_search)

        # Row 2: Table to display the database
        self.view_db_table = QTableWidget()
        self.view_db_table.setStyleSheet("""
            QTableWidget {
                color: #000000;
                border: 0.5px solid #a3a3a3;
                border-radius: 0px;
                background: white;
            }
        """)
        self.view_db_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        container_layout.addLayout(row_top)
        container_layout.addWidget(self.view_db_table)

        # Load the database into the table (if DB path is set)
        self.load_database()

        return container




    def build_search_page(self, title_text):
        """
        Builds Daily / Monthly / Annual pages:
        - Row 1: Search bar + button
        - Row 2: Placeholder content area (e.g., chart area)
        """
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(12)

        # Row 1: search bar
        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 12)
        search_input = QLineEdit()
        search_input.setFixedWidth(450)
        search_input.setPlaceholderText(" Insira a data ...")
        search_input.setMinimumHeight(50)
        search_input.setFont(QFont("Segoe UI", 16))
        search_input.setStyleSheet("""
            QLineEdit {
                color: #a3a3a3;
                background: white;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLineEdit:hover { background: #f2f2f2; }
        """)

        btn_search = QPushButton("Pesquisar")
        btn_search.setMinimumHeight(50)
        btn_search.setFont(QFont("Segoe UI", 16))
        btn_search.setStyleSheet("""
            QPushButton {
                color: #a3a3a3;
                font-weight: 600;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                background: #ffffff;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #f2f2f2; }
        """)
        row_top.addStretch()
        row_top.addWidget(search_input)
        row_top.addSpacing(8)
        row_top.addWidget(btn_search)
        # row_top.addStretch()

        # Row 2: placeholder content
        placeholder = QTextEdit()
        placeholder.setReadOnly(True)
        placeholder.setText(f"O conteudo dos {title_text} vai aparecer aquí")
        placeholder.setMinimumHeight(300)
        placeholder.setFont(QFont("sans-serif", 18))

        layout.addLayout(row_top)
        layout.addWidget(placeholder)

        return container
    
    def load_database(self):
        if not self.db_path or not os.path.exists(self.db_path):
            return

        self.view_db_table.blockSignals(True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM dados_solares ORDER BY "Data-Hora" ASC;')
                rows = cursor.fetchall()
                headers = [description[0] for description in cursor.description]

            self.view_db_table.setColumnCount(len(headers))
            self.view_db_table.setRowCount(len(rows))
            self.view_db_table.setHorizontalHeaderLabels(headers)

            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    text = "" if value is None else str(value)
                    item = QTableWidgetItem(text)

                    if c == 0:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    else:
                        item.setFlags(item.flags() | Qt.ItemIsEditable)

                    item.setData(Qt.UserRole, False)
                    self.view_db_table.setItem(r, c, item)

            header = self.view_db_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)

            try:
                self.view_db_table.itemChanged.disconnect(self.on_item_changed)
            except TypeError:
                pass

            self.view_db_table.itemChanged.connect(self.on_item_changed)

            self.unsaved_changes = False

        except sqlite3.Error as e:
            self.mostrar_erro("Falha ao carregar o banco de dados.", e)

        finally:
            self.view_db_table.blockSignals(False)


    def on_item_changed(self, item):
        # Apenas colunas editáveis (Pira1 e Pira2)
        if item.column() in (1, 2):
            self.unsaved_changes = True

            # Marca a linha como modificada
            row = item.row()
            for col in range(self.view_db_table.columnCount()):
                table_item = self.view_db_table.item(row, col)
                if table_item:
                    table_item.setData(Qt.UserRole, True)

    def show_page(self, name):
        new_index = self.page_indexes.get(name, 0)
        current_index = self.pages.currentIndex()

        # If user is leaving "Base de Dados" page with unsaved changes
        if current_index == self.page_indexes["view_db"] and new_index != current_index and self.unsaved_changes:
            file_name = os.path.basename(self.db_path) if self.db_path else "o arquivo"

            dialog = SaveChangesDialog(file_name, self)
            dialog.exec_()

            if dialog.choice == "salvar":
                saved = self.save_changes_to_database(show_message=False)
                if not saved:
                    return  # stay on current page if save failed

            elif dialog.choice == "nao_salvar":
                self.load_database()  # restore original data from DB

            else:
                return  # cancelar => do not change page

        self.pages.setCurrentIndex(new_index)

    def clear_modified_flags(self):
        for row in range(self.view_db_table.rowCount()):
            for col in range(self.view_db_table.columnCount()):
                item = self.view_db_table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, False)

        self.unsaved_changes = False

    def save_changes_to_database(self, show_message=True):
        if not self.db_path:
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                modified_rows = 0

                for row in range(self.view_db_table.rowCount()):
                    row_modified = any(
                        self.view_db_table.item(row, col) and
                        self.view_db_table.item(row, col).data(Qt.UserRole)
                        for col in range(self.view_db_table.columnCount())
                    )

                    if not row_modified:
                        continue

                    date_item = self.view_db_table.item(row, 0)
                    pira1_item = self.view_db_table.item(row, 1)
                    pira2_item = self.view_db_table.item(row, 2)

                    if not (date_item and pira1_item and pira2_item):
                        continue

                    try:
                        date_value = date_item.text().strip()

                        pira1_text = pira1_item.text().strip()
                        pira2_text = pira2_item.text().strip()

                        pira1_value = float(pira1_text) if pira1_text else None
                        pira2_value = float(pira2_text) if pira2_text else None

                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Valor inválido",
                            f"Valores inválidos na linha {row + 1}. Corrija antes de salvar."
                        )
                        return False

                    cursor.execute("""
                        INSERT INTO dados_solares
                        ("Data-Hora", "Sample Av Pira1[W/m2]", "Sample Av Pira2[W/m2]")
                        VALUES (?, ?, ?)
                        ON CONFLICT("Data-Hora") DO UPDATE SET
                            "Sample Av Pira1[W/m2]" = excluded."Sample Av Pira1[W/m2]",
                            "Sample Av Pira2[W/m2]" = excluded."Sample Av Pira2[W/m2]";
                    """, (date_value, pira1_value, pira2_value))

                    modified_rows += 1

                conn.commit()

            self.clear_modified_flags()

            if show_message:
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"{modified_rows} registro(s) salvo(s) com sucesso!"
                )

            return True

        except sqlite3.Error as e:
            self.mostrar_erro("Erro ao salvar as alterações.", e)
            return False

    def on_save_close(self):
        file_name = os.path.basename(self.db_path) if self.db_path else "o arquivo"

        if not self.unsaved_changes:
            self.return_to_start_callback()
            return

        dialog = SaveChangesDialog(file_name, self)
        dialog.exec_()

        if dialog.choice == "salvar":
            saved = self.save_changes_to_database(show_message=True)
            if saved:
                self.return_to_start_callback()

        elif dialog.choice == "nao_salvar":
            self.unsaved_changes = False
            self.load_database()
            self.return_to_start_callback()

        # cancelar => do nothing

    def import_excel_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione um arquivo Excel",
            "",
            "Arquivos Excel (*.xlsx *.xls);;Todos os arquivos (*)"
        )

        if not file_path:
            return

        settings_dialog = ImportSettingsDialog(self)

        if settings_dialog.exec_() != QDialog.Accepted:
            return

        settings = settings_dialog.get_values()

        latitude = settings["latitude"]
        interval_minutes = settings["interval_minutes"]
        start_date = settings["start_date"]
        end_date = settings["end_date"]

        if end_date < start_date:
            QMessageBox.warning(
                self,
                "Datas inválidas",
                "A data final não pode ser menor que a data inicial."
            )
            return

        try:
            
            # First sunrise and last sunset only for showing the second window
            first_sunrise, _ = calculate_sunrise_sunset(start_date, latitude)
            _, last_sunset = calculate_sunrise_sunset(end_date, latitude)

            first_sunrise = round_up_to_interval(first_sunrise, interval_minutes)
            last_sunset = round_down_to_interval(last_sunset, interval_minutes)

            solar_dialog = SolarHourDialog(first_sunrise, last_sunset, self)

            if solar_dialog.exec_() != QDialog.Accepted: 
                return

            solar_hours = solar_dialog.get_values()

            custom_start_time = solar_hours["start_time"]
            custom_end_time = solar_hours["end_time"]

            overwrite_dialog = OverwriteDialog(self)

            if overwrite_dialog.exec_() != QDialog.Accepted:
                return

            overwrite_existing = overwrite_dialog.choice == "overwrite"

            if start_date == end_date and custom_end_time <= custom_start_time:
                QMessageBox.warning(
                    self,
                    "Horários inválidos",
                    "Para uma única data, a hora final deve ser maior que a hora inicial."
                )
                return

            def find_header_row(file_path):
                df_raw = pd.read_excel(file_path, header=None)

                for i, row in df_raw.iterrows():
                    lower_row = [str(cell).lower().strip() for cell in row]

                    if ("date-hour" in lower_row or "data-hora" in lower_row) and \
                    any("pira1" in c for c in lower_row) and \
                    any("pira2" in c for c in lower_row):
                        return i

                return None

            header_row = find_header_row(file_path)

            if header_row is None:
                QMessageBox.critical(
                    self,
                    "Arquivo Inválido",
                    "Cabeçalho com 'date-hour', 'pira1' e 'pira2' não encontrado."
                )
                return

            df = pd.read_excel(file_path, header=header_row, dtype=str)
            cols_lower = [str(c).lower().strip() for c in df.columns]

            date_col = next(
                (df.columns[i] for i, c in enumerate(cols_lower)
                if c in ["date-hour", "data-hora"]),
                None
            )

            pira1_col = next(
                (df.columns[i] for i, c in enumerate(cols_lower)
                if "pira1" in c),
                None
            )

            pira2_col = next(
                (df.columns[i] for i, c in enumerate(cols_lower)
                if "pira2" in c),
                None
            )

            if not (date_col and pira1_col and pira2_col):
                QMessageBox.critical(
                    self,
                    "Arquivo Inválido",
                    "O arquivo não contém todas as informações necessárias."
                )
                return

            # Create parsed date column
            df["_parsed_date"] = pd.to_datetime(
                df[date_col],
                format="%y/%m/%d %H:%M:%S",
                errors="coerce"
            )

            df = df.dropna(subset=["_parsed_date"])

            # Convert Excel rows into dictionary
            excel_data = {}

            for _, row in df.iterrows():
                date_value = row["_parsed_date"]

                pira1_value = pd.to_numeric(row[pira1_col], errors="coerce")
                pira2_value = pd.to_numeric(row[pira2_col], errors="coerce")

                if pd.isna(pira1_value) or pd.isna(pira2_value):
                    continue

                if pira1_value < 0 or pira2_value < 0:
                    continue

                date_key = date_value.strftime("%Y-%m-%d %H:%M:%S")
                excel_data[date_key] = (float(pira1_value), float(pira2_value))

            expected_times = generate_expected_intervals(
                start_date=start_date,
                end_date=end_date,
                latitude=latitude,
                interval_minutes=interval_minutes,
                custom_start_time=custom_start_time,
                custom_end_time=custom_end_time
            )

            self.view_db_table.blockSignals(True)

            try:
                existing_dates = {
                    self.view_db_table.item(r, 0).text()
                    for r in range(self.view_db_table.rowCount())
                    if self.view_db_table.item(r, 0)
                }

                imported_rows = 0
                real_value_rows = 0
                null_value_rows = 0

                for dt in expected_times:
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")

                    if date_str in existing_dates:
                        if not overwrite_existing:
                            continue

                        if date_str not in excel_data:
                            continue

                        pira1_value, pira2_value = excel_data[date_str]

                        for row in range(self.view_db_table.rowCount()):
                            item = self.view_db_table.item(row, 0)

                            if item and item.text() == date_str:

                                self.view_db_table.item(row, 1).setText(str(pira1_value))
                                self.view_db_table.item(row, 2).setText(str(pira2_value))

                                for col in range(self.view_db_table.columnCount()):
                                    self.view_db_table.item(row, col).setData(Qt.UserRole, True)

                                imported_rows += 1
                                real_value_rows += 1
                                break

                        continue

                    if date_str in excel_data:
                        pira1_value, pira2_value = excel_data[date_str]
                        real_value_rows += 1
                    else:
                        pira1_value, pira2_value = None, None
                        null_value_rows += 1

                    row_position = self.view_db_table.rowCount()
                    self.view_db_table.insertRow(row_position)

                    date_item = QTableWidgetItem(date_str)
                    date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                    date_item.setData(Qt.UserRole, True)

                    pira1_text = "" if pira1_value is None else str(pira1_value)
                    pira2_text = "" if pira2_value is None else str(pira2_value)

                    pira1_item = QTableWidgetItem(pira1_text)
                    pira2_item = QTableWidgetItem(pira2_text)

                    pira1_item.setData(Qt.UserRole, True)
                    pira2_item.setData(Qt.UserRole, True)

                    self.view_db_table.setItem(row_position, 0, date_item)
                    self.view_db_table.setItem(row_position, 1, pira1_item)
                    self.view_db_table.setItem(row_position, 2, pira2_item)

                    existing_dates.add(date_str)
                    imported_rows += 1

            finally:
                self.view_db_table.blockSignals(False)

            self.view_db_table.sortItems(0, Qt.AscendingOrder)

            if imported_rows > 0:
                self.unsaved_changes = True

                QMessageBox.information(
                    self,
                    "Importação Concluída",
                    f"{imported_rows} dados importados com sucesso.\n\n"
                    f"Registros com dados reais do Excel: {real_value_rows}\n"
                    f"Registros sem medição (NULL): {null_value_rows}\n\n"
                    "Os dados ainda não foram salvos no banco. Clique em 'Salvar e Sair' e escolha 'Salvar' para gravar as alterações."
                )
            else:
                QMessageBox.information(
                    self,
                    "Importação",
                    "Nenhum dado novo foi importado."
                )

        except Exception as e:
            self.mostrar_erro(
                "Erro ao importar os dados do Excel. Verifique o arquivo.",
                e
            )


    def search_in_table(self, search_text):
        """Search for a date (or substring) inside the 'Data-Hora' column and scroll to it."""
        if not search_text.strip():
            QMessageBox.information(self, "Pesquisar", "Digite uma data para pesquisar.")
            return

        table = self.view_db_table
        rows = table.rowCount()

        if rows == 0:
            QMessageBox.information(self, "Pesquisar", "A tabela está vazia.")
            return

        # Find matches (case-insensitive, partial)
        found_row = None
        for r in range(rows):
            item = table.item(r, 0)  # column 0 = "Data-Hora"
            if item and search_text.lower() in item.text().lower():
                found_row = r
                break

        if found_row is not None:
            table.selectRow(found_row)
            table.scrollToItem(table.item(found_row, 0), QTableWidget.PositionAtCenter)
        else:
            QMessageBox.information(self, "Pesquisar", f"Nenhum registro encontrado para '{search_text}'.")

    def closeEvent(self, event):
        if self.returning_to_start:
            event.accept()
            return

        if not self.unsaved_changes:
            self.returning_to_start = True
            self.return_to_start_callback()
            event.ignore()
            return

        file_name = os.path.basename(self.db_path) if self.db_path else "o arquivo"

        dialog = SaveChangesDialog(file_name, self)
        dialog.exec_()

        if dialog.choice == "salvar":
            saved = self.save_changes_to_database(show_message=True)

            if saved:
                self.returning_to_start = True
                self.return_to_start_callback()

            event.ignore()

        elif dialog.choice == "nao_salvar":
            self.unsaved_changes = False
            self.load_database()
            self.returning_to_start = True
            self.return_to_start_callback()
            event.ignore()

        else:
            event.ignore()

    def build_daily_page(self):
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 12)

        btn_load = QPushButton("Atualizar Resultados")
        btn_load.clicked.connect(self.update_daily_results)

        btn_load.setMinimumHeight(50)
        btn_load.setFont(QFont("Segoe UI", 16))
        btn_load.setStyleSheet("""
            QPushButton {
                color: #a3a3a3;
                font-weight: 600;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                background: white;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #f2f2f2; }
        """)

        search_input = QLineEdit()
        search_input.setFixedWidth(450)
        search_input.setPlaceholderText(" Insira a data ...")
        search_input.setMinimumHeight(50)
        search_input.setFont(QFont("Segoe UI", 16))
        search_input.setStyleSheet("""
            QLineEdit {
                color: #a3a3a3;
                background: white;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLineEdit:hover { background: #f2f2f2; }
        """)

        btn_search = QPushButton("Pesquisar")
        btn_search.clicked.connect(lambda: self.search_in_daily_table(search_input.text()))
        btn_search.setMinimumHeight(50)
        btn_search.setFont(QFont("Segoe UI", 16))
        btn_search.setStyleSheet(btn_load.styleSheet())

        row_top.addWidget(btn_load)
        row_top.addStretch()
        row_top.addWidget(search_input)
        row_top.addSpacing(8)
        row_top.addWidget(btn_search)

        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(4)
        self.daily_table.setRowCount(0)
        self.daily_table.setHorizontalHeaderLabels([
            "Data",
            "H W.h/m²",
            "Ho W.h/m²",
            "kt diário"
        ])

        self.daily_table.setStyleSheet("""
            QTableWidget {
                color: #000000;
                border: 0.5px solid #a3a3a3;
                background: white;
            }
        """)

        self.daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.daily_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addLayout(row_top)
        layout.addWidget(self.daily_table)

        return container


    def calculate_declination(self, n):
        return 23.45 * math.sin(math.radians((360 / 365.24) * (284 + n)))


    def calculate_daily_ho(self, current_date, latitude_deg):
        Gsc = 1367  # W/m²
        n = current_date.timetuple().tm_yday

        declination_deg = self.calculate_declination(n)

        latitude_rad = math.radians(latitude_deg)
        declination_rad = math.radians(declination_deg)

        cos_wss = -math.tan(latitude_rad) * math.tan(declination_rad)
        cos_wss = max(-1, min(1, cos_wss))

        wss_rad = math.acos(cos_wss)
        wss_deg = math.degrees(wss_rad)

        ho = (
            (24 / math.pi)
            * Gsc
            * (1 + 0.033 * math.cos(math.radians((360 * n) / 365.24)))
            * (
                math.cos(latitude_rad)
                * math.cos(declination_rad)
                * math.sin(wss_rad)
                +
                (math.pi * wss_deg / 180)
                * math.sin(latitude_rad)
                * math.sin(declination_rad)
            )
        )

        return ho
    

    def update_daily_results(self):
        dialog = DailyResultsDialog(self)

        if dialog.exec_() != QDialog.Accepted:
            return

        values = dialog.get_values()
        latitude = values["latitude"]
        interval_minutes = values["interval_minutes"]

        if not self.db_path or not os.path.exists(self.db_path):
            QMessageBox.warning(self, "Erro", "Nenhum banco de dados foi aberto.")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        "Data-Hora",
                        "Sample Av Pira1[W/m2]",
                        "Sample Av Pira2[W/m2]"
                    FROM dados_solares
                    WHERE 
                        "Sample Av Pira1[W/m2]" IS NOT NULL
                        AND "Sample Av Pira2[W/m2]" IS NOT NULL
                    ORDER BY "Data-Hora" ASC;
                """)
                rows = cursor.fetchall()

            daily_data = {}

            for date_text, pira1, pira2 in rows:
                try:
                    dt = datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue

                day = dt.date()
                average_pira = (float(pira1) + float(pira2)) / 2

                if day not in daily_data:
                    daily_data[day] = []

                daily_data[day].append(average_pira)

            self.daily_table.setRowCount(0)

            for day in sorted(daily_data.keys()):
                averages = daily_data[day]

                H = (interval_minutes / 60) * sum(averages)
                Ho = self.calculate_daily_ho(day, latitude)

                kt = H / Ho if Ho != 0 else 0

                row_position = self.daily_table.rowCount()
                self.daily_table.insertRow(row_position)

                self.daily_table.setItem(row_position, 0, QTableWidgetItem(day.strftime("%Y-%m-%d")))
                self.daily_table.setItem(row_position, 1, QTableWidgetItem(f"{H:.4f}"))
                self.daily_table.setItem(row_position, 2, QTableWidgetItem(f"{Ho:.4f}"))
                self.daily_table.setItem(row_position, 3, QTableWidgetItem(f"{kt:.4f}"))

            QMessageBox.information(
                self,
                "Resultados atualizados",
                f"{len(daily_data)} resultado(s) diário(s) calculado(s) com sucesso."
            )

        except Exception as e:
            self.mostrar_erro("Erro ao atualizar os resultados diários.", e)


    def search_in_daily_table(self, search_text):
        if not search_text.strip():
            QMessageBox.information(self, "Pesquisar", "Digite uma data para pesquisar.")
            return

        table = self.daily_table
        rows = table.rowCount()

        if rows == 0:
            QMessageBox.information(self, "Pesquisar", "A tabela de resultados diários está vazia.")
            return

        found_row = None

        for r in range(rows):
            item = table.item(r, 0)  # coluna 0 = Data

            if item and search_text.lower() in item.text().lower():
                found_row = r
                break

        if found_row is not None:
            table.selectRow(found_row)
            table.scrollToItem(table.item(found_row, 0), QTableWidget.PositionAtCenter)
        else:
            QMessageBox.information(
                self,
                "Pesquisar",
                f"Nenhum resultado diário encontrado para '{search_text}'."
            )

    
    def build_monthly_page(self):
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 12)

        btn_load = QPushButton("Atualizar Resultados")
        btn_load.clicked.connect(self.update_monthly_results)
        btn_load.setMinimumHeight(50)
        btn_load.setFont(QFont("Segoe UI", 16))
        btn_load.setStyleSheet("""
            QPushButton {
                color: #a3a3a3;
                font-weight: 600;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                background: white;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #f2f2f2; }
        """)

        search_input = QLineEdit()
        search_input.setFixedWidth(450)
        search_input.setPlaceholderText(" Insira o ano/mês ...")
        search_input.setMinimumHeight(50)
        search_input.setFont(QFont("Segoe UI", 16))
        search_input.setStyleSheet("""
            QLineEdit {
                color: #a3a3a3;
                background: white;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLineEdit:hover { background: #f2f2f2; }
        """)

        btn_search = QPushButton("Pesquisar")
        btn_search.clicked.connect(lambda: self.search_in_monthly_table(search_input.text()))
        btn_search.setMinimumHeight(50)
        btn_search.setFont(QFont("Segoe UI", 16))
        btn_search.setStyleSheet(btn_load.styleSheet())

        row_top.addWidget(btn_load)
        row_top.addStretch()
        row_top.addWidget(search_input)
        row_top.addSpacing(8)
        row_top.addWidget(btn_search)

        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(4)
        self.monthly_table.setRowCount(0)
        self.monthly_table.setHorizontalHeaderLabels([
            "Data ano/mês",
            "H mensal W.h/m²",
            "Ho mensal W.h/m²",
            "Kt mensal"
        ])

        self.monthly_table.setStyleSheet("""
            QTableWidget {
                color: #000000;
                border: 0.5px solid #a3a3a3;
                background: white;
            }
        """)

        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addLayout(row_top)
        layout.addWidget(self.monthly_table)

        return container
    

    def update_monthly_results(self):
        if self.daily_table.rowCount() == 0:
            QMessageBox.information(
                self,
                "Resultados mensais",
                "Primeiro atualize os resultados diários."
            )
            return

        monthly_data = {}

        for row in range(self.daily_table.rowCount()):
            date_item = self.daily_table.item(row, 0)
            h_item = self.daily_table.item(row, 1)
            ho_item = self.daily_table.item(row, 2)

            if not (date_item and h_item and ho_item):
                continue

            try:
                day = datetime.strptime(date_item.text().strip(), "%Y-%m-%d").date()
                H = float(h_item.text().strip())
                Ho = float(ho_item.text().strip())
            except ValueError:
                continue

            month_key = day.strftime("%Y-%m")

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "H_values": [],
                    "Ho_values": []
                }

            monthly_data[month_key]["H_values"].append(H)
            monthly_data[month_key]["Ho_values"].append(Ho)

        self.monthly_table.setRowCount(0)

        for month_key in sorted(monthly_data.keys()):
            H_values = monthly_data[month_key]["H_values"]
            Ho_values = monthly_data[month_key]["Ho_values"]

            H_monthly = sum(H_values) / len(H_values)
            Ho_monthly = sum(Ho_values) / len(Ho_values)

            kt_monthly = H_monthly / Ho_monthly if Ho_monthly != 0 else 0

            row_position = self.monthly_table.rowCount()
            self.monthly_table.insertRow(row_position)

            self.monthly_table.setItem(row_position, 0, QTableWidgetItem(month_key))
            self.monthly_table.setItem(row_position, 1, QTableWidgetItem(f"{H_monthly:.4f}"))
            self.monthly_table.setItem(row_position, 2, QTableWidgetItem(f"{Ho_monthly:.4f}"))
            self.monthly_table.setItem(row_position, 3, QTableWidgetItem(f"{kt_monthly:.4f}"))

        QMessageBox.information(
            self,
            "Resultados atualizados",
            f"{len(monthly_data)} resultado(s) mensal(is) calculado(s) com sucesso."
        )


    def search_in_monthly_table(self, search_text):
        if not search_text.strip():
            QMessageBox.information(self, "Pesquisar", "Digite um ano/mês para pesquisar.")
            return

        table = self.monthly_table
        rows = table.rowCount()

        if rows == 0:
            QMessageBox.information(self, "Pesquisar", "A tabela de resultados mensais está vazia.")
            return

        found_row = None

        for r in range(rows):
            item = table.item(r, 0)  # coluna 0 = Data ano/mês

            if item and search_text.lower() in item.text().lower():
                found_row = r
                break

        if found_row is not None:
            table.selectRow(found_row)
            table.scrollToItem(table.item(found_row, 0), QTableWidget.PositionAtCenter)
        else:
            QMessageBox.information(
                self,
                "Pesquisar",
                f"Nenhum resultado mensal encontrado para '{search_text}'."
            )


    def build_annual_page(self):
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 12)

        btn_load = QPushButton("Atualizar Resultados")
        btn_load.clicked.connect(self.update_annual_results)
        btn_load.setMinimumHeight(50)
        btn_load.setFont(QFont("Segoe UI", 16))
        btn_load.setStyleSheet("""
            QPushButton {
                color: #a3a3a3;
                font-weight: 600;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                background: white;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #f2f2f2; }
        """)

        search_input = QLineEdit()
        search_input.setFixedWidth(450)
        search_input.setPlaceholderText(" Insira o ano ...")
        search_input.setMinimumHeight(50)
        search_input.setFont(QFont("Segoe UI", 16))
        search_input.setStyleSheet("""
            QLineEdit {
                color: #a3a3a3;
                background: white;
                border: 2px solid #a3a3a3;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLineEdit:hover { background: #f2f2f2; }
        """)

        btn_search = QPushButton("Pesquisar")
        btn_search.clicked.connect(lambda: self.search_in_annual_table(search_input.text()))
        btn_search.setMinimumHeight(50)
        btn_search.setFont(QFont("Segoe UI", 16))
        btn_search.setStyleSheet(btn_load.styleSheet())

        row_top.addWidget(btn_load)
        row_top.addStretch()
        row_top.addWidget(search_input)
        row_top.addSpacing(8)
        row_top.addWidget(btn_search)

        self.annual_table = QTableWidget()
        self.annual_table.setColumnCount(4)
        self.annual_table.setRowCount(0)
        self.annual_table.setHorizontalHeaderLabels([
            "Ano",
            "H anual W.h/m²",
            "Ho anual W.h/m²",
            "Kt anual"
        ])

        self.annual_table.setStyleSheet("""
            QTableWidget {
                color: #000000;
                border: 0.5px solid #a3a3a3;
                background: white;
            }
        """)

        self.annual_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.annual_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addLayout(row_top)
        layout.addWidget(self.annual_table)

        return container
    


    def update_annual_results(self):
        if self.daily_table.rowCount() == 0:
            QMessageBox.information(
                self,
                "Resultados anuais",
                "Primeiro atualize os resultados diários."
            )
            return

        annual_data = {}

        for row in range(self.daily_table.rowCount()):
            date_item = self.daily_table.item(row, 0)
            h_item = self.daily_table.item(row, 1)
            ho_item = self.daily_table.item(row, 2)

            if not (date_item and h_item and ho_item):
                continue

            try:
                day = datetime.strptime(date_item.text().strip(), "%Y-%m-%d").date()
                H = float(h_item.text().strip())
                Ho = float(ho_item.text().strip())
            except ValueError:
                continue

            year_key = day.strftime("%Y")

            if year_key not in annual_data:
                annual_data[year_key] = {
                    "H_values": [],
                    "Ho_values": []
                }

            annual_data[year_key]["H_values"].append(H)
            annual_data[year_key]["Ho_values"].append(Ho)

        self.annual_table.setRowCount(0)

        for year_key in sorted(annual_data.keys()):
            H_values = annual_data[year_key]["H_values"]
            Ho_values = annual_data[year_key]["Ho_values"]

            H_annual = sum(H_values) / len(H_values)
            Ho_annual = sum(Ho_values) / len(Ho_values)

            kt_annual = H_annual / Ho_annual if Ho_annual != 0 else 0

            row_position = self.annual_table.rowCount()
            self.annual_table.insertRow(row_position)

            self.annual_table.setItem(row_position, 0, QTableWidgetItem(year_key))
            self.annual_table.setItem(row_position, 1, QTableWidgetItem(f"{H_annual:.4f}"))
            self.annual_table.setItem(row_position, 2, QTableWidgetItem(f"{Ho_annual:.4f}"))
            self.annual_table.setItem(row_position, 3, QTableWidgetItem(f"{kt_annual:.4f}"))

        QMessageBox.information(
            self,
            "Resultados atualizados",
            f"{len(annual_data)} resultado(s) anual(is) calculado(s) com sucesso."
        )

    
    def search_in_annual_table(self, search_text):
        if not search_text.strip():
            QMessageBox.information(self, "Pesquisar", "Digite um ano para pesquisar.")
            return

        table = self.annual_table
        rows = table.rowCount()

        if rows == 0:
            QMessageBox.information(self, "Pesquisar", "A tabela de resultados anuais está vazia.")
            return

        found_row = None

        for r in range(rows):
            item = table.item(r, 0)  # coluna 0 = Ano

            if item and search_text.lower() in item.text().lower():
                found_row = r
                break

        if found_row is not None:
            table.selectRow(found_row)
            table.scrollToItem(table.item(found_row, 0), QTableWidget.PositionAtCenter)
        else:
            QMessageBox.information(
                self,
                "Pesquisar",
                f"Nenhum resultado anual encontrado para '{search_text}'."
            )

class AppController:
    def __init__(self):
        self.start_window = None
        self.main_window = None
        self.db_path = None

    def show_start(self):
        if not self.start_window:
            self.start_window = StartWindow(self.show_main, self)
        self.start_window.show()

    def show_main(self):
        if self.start_window:
            self.start_window.hide()

        # Always create a new main window with the current db_path
        self.main_window = MainAppWindow(self.return_to_start, self.db_path)
        self.main_window.show()

    def return_to_start(self):
        if self.main_window:
            self.main_window.hide()
            self.main_window.deleteLater()
            self.main_window = None

        if self.start_window:
            self.start_window.show()

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("images/solarimetro_icon.icns")))
    screen = app.primaryScreen()
    size = screen.size()
    app.setStyle("Fusion")
    controller = AppController()
    controller.show_start()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()