import sys
import os
import json
import re
import winreg
import subprocess
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QPushButton, QFileDialog,
                             QMessageBox, QMenu, QAbstractItemView, QListWidgetItem,
                             QStyle, QStyleFactory, QMenuBar, QAction, QStyledItemDelegate,
                             QStyleOptionViewItem, QToolTip, QSizePolicy, QLineEdit, QDialog,
                             QLabel, QDialogButtonBox, QSpinBox, QCheckBox, QComboBox,
                             QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QPoint, pyqtSignal, QUrl, QSettings, QEvent
from PyQt5.QtGui import (QIcon, QPixmap, QPainter, QPen, QColor, QFontDatabase,
                         QFont, QBrush, QPalette, QCursor)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import ctypes
import ctypes.wintypes

# ========== Работа с версиями ==========
def get_file_version(file_path):
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(file_path, None)
        if size == 0: return None
        buffer = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(file_path, 0, size, buffer)

        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [
                ("dwSignature", ctypes.c_uint), ("dwStrucVersion", ctypes.c_uint),
                ("dwFileVersionMS", ctypes.c_uint), ("dwFileVersionLS", ctypes.c_uint),
                ("dwProductVersionMS", ctypes.c_uint), ("dwProductVersionLS", ctypes.c_uint),
                ("dwFileFlagsMask", ctypes.c_uint), ("dwFileFlags", ctypes.c_uint),
                ("dwFileOS", ctypes.c_uint), ("dwFileType", ctypes.c_uint),
                ("dwFileSubtype", ctypes.c_uint), ("dwFileDateMS", ctypes.c_uint),
                ("dwFileDateLS", ctypes.c_uint),
            ]

        ptr = ctypes.c_void_p()
        ctypes.windll.version.VerQueryValueW(buffer, "\\", ctypes.byref(ptr), ctypes.byref(ctypes.c_uint()))
        info = ctypes.cast(ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents

        major = (info.dwFileVersionMS >> 16) & 0xFFFF
        minor = info.dwFileVersionMS & 0xFFFF
        patch = (info.dwFileVersionLS >> 16) & 0xFFFF
        return f"{major}.{minor}.{patch}"
    except Exception:
        return None

def parse_version(v):
    parts = v.split('.')
    return tuple(int(p) for p in parts[:3])

def compare_versions(v1, v2):
    t1 = parse_version(v1); t2 = parse_version(v2)
    for a, b in zip(t1, t2):
        if a > b: return 1
        elif a < b: return -1
    if len(t1) > len(t2): return 1
    elif len(t1) < len(t2): return -1
    return 0

def strip_bbcode(text):
    if not text: return ''
    return re.sub(r'\[/?[^\]]+\]', '', text)

# ========== Локализация ==========
LANGUAGES = {
    'ru': {
        'window_title': 'Менеджер модов Kenshi',
        'menu_file': 'Файл', 'menu_load_cfg': 'Загрузить CFG', 'menu_backup': 'Сохранить',
        'menu_exit': 'Выход', 'menu_view': 'Вид', 'menu_refresh': 'Обновить список',
        'menu_help': 'Справка', 'menu_about': 'О программе', 'menu_settings': 'Настройки',
        'about_text': (
            'Упрощённый менеджер модов для Kenshi.\n\n'
            'Возможности:\n'
            '• Включать/выключать моды (ПКМ по моду)\n'
            '• Изменять порядок загрузки перетаскиванием (drag‑and‑drop)\n'
            '• Множественный выбор через Shift для перетаскивания группы\n'
            '• Перетаскивание между секциями автоматически включает/выключает моды\n'
            '• Автоматическое сканирование локальных модов и модов из Steam Workshop\n'
            '• Всплывающие карточки модов с изображением, названием и описанием\n'
            '• Проверка зависимостей и подсветка конфликтов\n'
            '• Сохранение порядка в mods.cfg\n'
            '• Загрузка временного списка из любого .cfg файла\n'
            '• Быстрый поиск с автопрокруткой и очисткой\n'
            '• Открытие страниц модов в Steam Workshop\n'
            '• Запуск игры (через Steam или напрямую)'
        ),
        'btn_save': 'Сохранить порядок модов', 'btn_launch': 'Запустить игру', 'btn_lang': 'ENG',
        'github_url': 'https://github.com/p4vl0-dev/kenshi-simple-mod-manager',
        'search_placeholder': 'Поиск мода...',
        'header_enabled': 'Включенные моды', 'header_disabled': 'Выключенные моды',
        'status_init': 'Инициализация...',
        'status_found_kenshi': 'Найдена Kenshi: {}', 'status_not_found_kenshi': 'Kenshi не найдена автоматически.',
        'status_paths_not_set': 'Пути не найдены. Используйте Настройки → Путь к Kenshi.',
        'status_manual_cancel': 'Ручной ввод отменён.',
        'status_backup_created': 'Файл сохранён: {}', 'status_backup_failed': 'Не удалось сохранить файл: {}',
        'status_loaded_mods': 'Загружено {} модов (включено: {}, выключено: {})',
        'status_saved_mods': 'Сохранено {} модов в {}',
        'status_game_launched': 'Игра запущена.', 'status_game_running': 'Игра запущена и работает.',
        'status_mod_toggled': 'Мод "{}" {} (всего включено: {})',
        'mod_status_enabled': 'включён', 'mod_status_disabled': 'выключен',
        'status_cfg_loaded': 'Загружен временный список из {}. Нажмите "Сохранить порядок" для применения.',
        'status_mod_selected_workshop': 'Выбран мод "{}" (есть страница в Workshop)',
        'status_mod_selected_local': 'Выбран мод "{}" (локальный, нет страницы в Workshop)',
        'tooltip_workshop': 'Перейти по ссылке в Workshop',
        'tooltip_folder': 'Открыть папку мода',
        'tooltip_duplicate': 'Найдены дубликаты! Нажмите, чтобы проверить',
        'error_mods_folder': 'Папка mods не найдена.',
        'error_read_cfg': 'Не удалось прочитать mods.cfg:\n{}',
        'error_save_cfg': 'Не удалось сохранить файл:\n{}',
        'error_launch_game': 'Не удалось запустить игру:\n{}',
        'warning_no_mods': 'Не найдено ни одного мода (с файлом .mod).',
        'warning_missing_mods': 'Следующие моды из mods.cfg не найдены:\n{}',
        'question_confirm_refresh': 'Обновить список модов?',
        'question_workshop_manual': 'Автоматически не удалось найти workshop.\nУказать вручную?',
        'question_duplicates_save': 'Обнаружены дублирующиеся моды.\nВы уверены, что хотите сохранить список?\n(Будут записаны только выбранные моды)',
        'info_save_success': 'mods.cfg успешно обновлён!',
        'confirm_title': 'Подтверждение', 'error_title': 'Ошибка',
        'warning_title': 'Предупреждение', 'info_title': 'Информация',
        'duplicate_dialog_title': 'Дублирующиеся моды',
        'duplicate_dialog_label': 'Обнаружены следующие дубликаты:',
        'save_dialog_text': 'Вы внесли изменения в список модов. Что сделать?',
        'save_btn_save': 'Сохранить', 'save_btn_backup': 'Сохранить с бэкапом', 'save_btn_cancel': 'Отмена',
        'backup_choose_title': 'Сохранить mods.cfg как...',
        'backup_filter': 'CFG Files (*.cfg);;All Files (*)',
        'yes': 'Да', 'no': 'Нет',
        'update_available_title': 'Доступно обновление',
        'update_available_text': 'Доступна новая версия {version}.\n\nВы хотите перейти на страницу загрузки?',
        'settings_title': 'Настройки',
        'settings_lang': 'Язык интерфейса',
        'settings_hover_group': 'Всплывающие карточки модов',
        'settings_hover_enabled': 'Показывать карточку при наведении',
        'settings_hover_delay': 'Задержка появления (мс)',
        'settings_hover_hint': 'Карточка появляется при наведении на название мода. Для модов из Workshop отображается изображение, название и описание. Клик по изображению или названию открывает страницу в Workshop.',
        'settings_behavior_group': 'Поведение',
        'settings_close_after_launch': 'Закрывать менеджер после запуска игры',
        'settings_kenshi_path_group': 'Путь к Kenshi',
        'settings_kenshi_current': 'Текущий путь',
        'settings_kenshi_none': '(не задан)',
        'settings_change_path': 'Изменить путь...',
        'settings_last_cfg': 'Последний загруженный конфиг',
        'settings_none': '(нет)',
        'settings_save': 'Сохранить',
        'settings_cancel': 'Отмена',
        'hover_loading': 'Загрузка...',
        'hover_no_description': 'Описание отсутствует.',
        'hover_click_to_open': 'Нажмите, чтобы открыть страницу в Workshop',
    },
    'en': {
        'window_title': 'Kenshi Simple Mod Manager',
        'menu_file': 'File', 'menu_load_cfg': 'Load CFG', 'menu_backup': 'Save',
        'menu_exit': 'Exit', 'menu_view': 'View', 'menu_refresh': 'Refresh list',
        'menu_help': 'Help', 'menu_about': 'About', 'menu_settings': 'Settings',
        'about_text': (
            'Simplified mod manager for Kenshi.\n\n'
            'Features:\n'
            '• Enable/disable mods (right-click on mod)\n'
            '• Change load order by drag-and-drop\n'
            '• Multi-select via Shift for dragging a group\n'
            '• Dragging between sections automatically enables/disables mods\n'
            '• Automatic scanning of local and Steam Workshop mods\n'
            '• Hover cards with Workshop image, title and description\n'
            '• Dependency checking and conflict highlighting\n'
            '• Save order to mods.cfg\n'
            '• Load temporary list from any .cfg file\n'
            '• Fast search with auto-scroll and clear button\n'
            '• Open mod pages in Steam Workshop\n'
            '• Launch game (via Steam or directly)'
        ),
        'btn_save': 'Save mods order', 'btn_launch': 'Launch game', 'btn_lang': 'РУС',
        'github_url': 'https://github.com/p4vl0-dev/kenshi-simple-mod-manager',
        'search_placeholder': 'Search mod...',
        'header_enabled': 'Enabled mods', 'header_disabled': 'Disabled mods',
        'status_init': 'Initializing...',
        'status_found_kenshi': 'Kenshi found: {}', 'status_not_found_kenshi': 'Kenshi not found automatically.',
        'status_paths_not_set': 'Paths not set. Use Settings → Kenshi path.',
        'status_manual_cancel': 'Manual input cancelled.',
        'status_backup_created': 'File saved: {}', 'status_backup_failed': 'Failed to save file: {}',
        'status_loaded_mods': 'Loaded {} mods (enabled: {}, disabled: {})',
        'status_saved_mods': 'Saved {} mods to {}',
        'status_game_launched': 'Game launched.', 'status_game_running': 'Game is running.',
        'status_mod_toggled': 'Mod "{}" {} (total enabled: {})',
        'mod_status_enabled': 'enabled', 'mod_status_disabled': 'disabled',
        'status_cfg_loaded': 'Temporary list loaded from {}. Press "Save order" to apply.',
        'status_mod_selected_workshop': 'Selected mod "{}" (has Workshop page)',
        'status_mod_selected_local': 'Selected mod "{}" (local, no Workshop page)',
        'tooltip_workshop': 'Open in Workshop', 'tooltip_folder': 'Open mod folder',
        'tooltip_duplicate': 'Duplicates found! Click to check',
        'error_mods_folder': 'Mods folder not found.',
        'error_read_cfg': 'Failed to read mods.cfg:\n{}',
        'error_save_cfg': 'Failed to save file:\n{}',
        'error_launch_game': 'Failed to launch game:\n{}',
        'warning_no_mods': 'No mods found (with .mod file).',
        'warning_missing_mods': 'Following mods from mods.cfg not found:\n{}',
        'question_confirm_refresh': 'Refresh mod list?',
        'question_workshop_manual': 'Workshop could not be found automatically.\nSpecify manually?',
        'question_duplicates_save': 'Duplicate mods detected.\nAre you sure you want to save the list?\n(Only selected mods will be written)',
        'info_save_success': 'mods.cfg successfully updated!',
        'confirm_title': 'Confirm', 'error_title': 'Error',
        'warning_title': 'Warning', 'info_title': 'Information',
        'duplicate_dialog_title': 'Duplicate mods',
        'duplicate_dialog_label': 'Following duplicates found:',
        'save_dialog_text': 'You have made changes to the mod list. What to do?',
        'save_btn_save': 'Save', 'save_btn_backup': 'Save with backup', 'save_btn_cancel': 'Cancel',
        'backup_choose_title': 'Save mods.cfg as...',
        'backup_filter': 'CFG Files (*.cfg);;All Files (*)',
        'yes': 'Yes', 'no': 'No',
        'update_available_title': 'Update available',
        'update_available_text': 'A new version {version} is available.\n\nDo you want to go to the download page?',
        'settings_title': 'Settings',
        'settings_lang': 'Interface language',
        'settings_hover_group': 'Mod hover cards',
        'settings_hover_enabled': 'Show hover card',
        'settings_hover_delay': 'Show delay (ms)',
        'settings_hover_hint': 'The card appears when hovering over the mod name. For Workshop mods it shows image, title and description. Clicking the image or title opens the Workshop page.',
        'settings_behavior_group': 'Behavior',
        'settings_close_after_launch': 'Close manager after launching the game',
        'settings_kenshi_path_group': 'Kenshi path',
        'settings_kenshi_current': 'Current path',
        'settings_kenshi_none': '(not set)',
        'settings_change_path': 'Change path...',
        'settings_last_cfg': 'Last loaded config',
        'settings_none': '(none)',
        'settings_save': 'Save',
        'settings_cancel': 'Cancel',
        'hover_loading': 'Loading...',
        'hover_no_description': 'No description.',
        'hover_click_to_open': 'Click to open the Workshop page',
    }
}

# ========== Иконки ==========
class IconFactory:
    @staticmethod
    def create_check_icon():
        pixmap = QPixmap(16, 16); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(0, 200, 0)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 16, 16, 3, 3)
        p.setPen(QPen(Qt.white, 2))
        p.drawLine(4, 8, 7, 11); p.drawLine(7, 11, 12, 4)
        p.end(); return QIcon(pixmap)

    @staticmethod
    def create_cross_icon():
        pixmap = QPixmap(16, 16); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(200, 0, 0)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 16, 16, 3, 3)
        p.setPen(QPen(Qt.white, 2))
        p.drawLine(3, 3, 13, 13); p.drawLine(13, 3, 3, 13)
        p.end(); return QIcon(pixmap)

    @staticmethod
    def create_steam_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False): base = sys._MEIPASS
        local_ico = os.path.join(base, "icons", "steam_tray.ico")
        if os.path.exists(local_ico): return QIcon(local_ico)
        steam_path = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]; winreg.CloseKey(key)
        except: pass
        if steam_path:
            ico_path = os.path.join(steam_path, "public", "steam_tray.ico")
            if os.path.exists(ico_path): return QIcon(ico_path)
        for drive in [chr(d) + ":" for d in range(ord('C'), ord('Z')+1)]:
            for sub in [r"Program Files (x86)\Steam\public\steam_tray.ico", r"Program Files\Steam\public\steam_tray.ico"]:
                ico_path = os.path.join(drive, sub)
                if os.path.exists(ico_path): return QIcon(ico_path)
        return IconFactory._create_fallback_steam_icon()

    @staticmethod
    def _create_fallback_steam_icon():
        pixmap = QPixmap(16, 16); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(100, 150, 255)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 16, 16, 3, 3)
        p.setPen(QPen(Qt.white, 1))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "S")
        p.end(); return QIcon(pixmap)

    @staticmethod
    def create_folder_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False): base = sys._MEIPASS
        folder_path = os.path.join(base, "icons", "folder.webp")
        if os.path.exists(folder_path): return QIcon(folder_path)
        pixmap = QPixmap(16, 16); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(200, 180, 150)); p.setPen(QPen(QColor(140, 120, 100), 1))
        p.drawRoundedRect(2, 4, 12, 10, 2, 2)
        p.drawLine(4, 4, 6, 2); p.drawLine(6, 2, 10, 2); p.drawLine(10, 2, 12, 4)
        p.end(); return QIcon(pixmap)

    @staticmethod
    def create_duplicate_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False): base = sys._MEIPASS
        warning_path = os.path.join(base, "icons", "warning.webp")
        if os.path.exists(warning_path): return QIcon(warning_path)
        pixmap = QPixmap(16, 16); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(255, 200, 0)); p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawPolygon(QPoint(8, 2), QPoint(14, 14), QPoint(2, 14))
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.drawLine(8, 6, 8, 10); p.drawLine(8, 12, 8, 13)
        p.end(); return QIcon(pixmap)

    @staticmethod
    def create_github_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False): base = sys._MEIPASS
        github_path = os.path.join(base, "icons", "github.webp")
        if os.path.exists(github_path): return QIcon(github_path)
        pixmap = QPixmap(20, 20); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(255, 255, 255)); p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 20, 20)
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "G")
        p.end(); return QIcon(pixmap)

# ========== Кликабельный QLabel ==========
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

# ========== Делегат ==========
class ModItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.steam_icon = IconFactory.create_steam_icon()
        self.folder_icon = IconFactory.create_folder_icon()
        self.duplicate_icon = IconFactory.create_duplicate_icon()
        self.icon_size = 20
        self.dup_icon_size = 16
        self.hovered_index = None
        self.animating = False
        self.tooltip_workshop = "Перейти по ссылке в Workshop"
        self.tooltip_folder = "Открыть папку мода"
        self.tooltip_duplicate = "Найдены дубликаты! Нажмите, чтобы проверить"

    def set_tooltip_text(self, text):
        self.tooltip_workshop = text

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if not (index.flags() & Qt.ItemIsSelectable): return

        rect = option.rect
        mod_name = index.data(Qt.UserRole + 3) or index.data(Qt.DisplayRole)
        parent = self.parent()
        has_duplicate = bool(parent and hasattr(parent, 'mod_dubles') and mod_name in parent.mod_dubles)

        if has_duplicate:
            dup_rect = QRect(rect.right() - self.dup_icon_size - 5 - self.icon_size - 5,
                             rect.top() + (rect.height() - self.dup_icon_size) // 2,
                             self.dup_icon_size, self.dup_icon_size)
            self.duplicate_icon.paint(painter, dup_rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)

        workshop_id = index.data(Qt.UserRole)
        icon_rect = QRect(rect.right() - self.icon_size - 5,
                          rect.top() + (rect.height() - self.icon_size) // 2,
                          self.icon_size, self.icon_size)
        if workshop_id:
            size = self.icon_size
            if self.animating and self.hovered_index == index: size = self.icon_size + 4
            offset = (size - self.icon_size) // 2
            icon_rect = QRect(rect.right() - size - 5 - offset,
                              rect.top() + (rect.height() - size) // 2, size, size)
            self.steam_icon.paint(painter, icon_rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)
        else:
            self.folder_icon.paint(painter, icon_rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)

        if index.data(Qt.UserRole + 1):
            painter.save()
            painter.setPen(QPen(QColor(255, 255, 0), 1, Qt.DashLine))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()

    def helpEvent(self, event, view, option, index):
        if not (index.flags() & Qt.ItemIsSelectable): return False
        rect = option.rect
        mod_name = index.data(Qt.UserRole + 3) or index.data(Qt.DisplayRole)
        parent = self.parent()
        has_duplicate = bool(parent and hasattr(parent, 'mod_dubles') and mod_name in parent.mod_dubles)

        dup_rect = None
        if has_duplicate:
            dup_rect = QRect(rect.right() - self.dup_icon_size - 5 - self.icon_size - 5,
                             rect.top() + (rect.height() - self.dup_icon_size) // 2,
                             self.dup_icon_size, self.dup_icon_size)
        icon_rect = QRect(rect.right() - self.icon_size - 5,
                          rect.top() + (rect.height() - self.icon_size) // 2,
                          self.icon_size, self.icon_size)
        pos = event.pos()
        if dup_rect and dup_rect.contains(pos):
            QToolTip.showText(event.globalPos(), self.tooltip_duplicate); return True
        elif icon_rect.contains(pos):
            wid = index.data(Qt.UserRole)
            QToolTip.showText(event.globalPos(), self.tooltip_workshop if wid else self.tooltip_folder)
            return True
        QToolTip.hideText()
        return True

    def editorEvent(self, event, model, option, index):
        if not (index.flags() & Qt.ItemIsSelectable): return False
        rect = option.rect
        mod_name = index.data(Qt.UserRole + 3) or index.data(Qt.DisplayRole)
        parent = self.parent()
        has_duplicate = bool(parent and hasattr(parent, 'mod_dubles') and mod_name in parent.mod_dubles)

        dup_rect = None
        if has_duplicate:
            dup_rect = QRect(rect.right() - self.dup_icon_size - 5 - self.icon_size - 5,
                             rect.top() + (rect.height() - self.dup_icon_size) // 2,
                             self.dup_icon_size, self.dup_icon_size)
        icon_rect = QRect(rect.right() - self.icon_size - 5,
                          rect.top() + (rect.height() - self.icon_size) // 2,
                          self.icon_size, self.icon_size)

        if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
            if dup_rect and dup_rect.contains(event.pos()):
                if parent and hasattr(parent, 'mod_dubles'):
                    parent.hide_hover_card()
                    parent.show_duplicate_dialog(mod_name)
                return True
            if icon_rect.contains(event.pos()):
                workshop_id = index.data(Qt.UserRole)
                view = option.widget
                if workshop_id:
                    # Принудительно прячем карточку
                    if parent: parent.hide_hover_card()
                    self.animating = True; self.hovered_index = index
                    if view: view.viewport().update()
                    def open_url():
                        webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}")
                        self.animating = False; self.hovered_index = None
                        if view: view.viewport().update()
                    QTimer.singleShot(150, open_url); return True
                else:
                    mod_path = parent.mod_paths.get(mod_name) if parent else None
                    if mod_path and os.path.exists(mod_path):
                        if parent: parent.hide_hover_card()
                        if sys.platform == 'win32': os.startfile(mod_path)
                        else: subprocess.Popen(['xdg-open', mod_path])
                    return True
        return False

# ========== Диалог дубликатов ==========
class DuplicateDialog(QDialog):
    def __init__(self, mod_name, duplicates, parent=None):
        super().__init__(parent)
        self.setWindowTitle(parent.str['duplicate_dialog_title'] if parent else "Duplicate mods")
        self.setMinimumSize(500, 300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(parent.str['duplicate_dialog_label'] if parent else "Found duplicates:"))
        self.list_widget = QListWidget()
        for dup in duplicates:
            info = dup.get('info')
            title = info.get('title') if info else None
            file_name = mod_name
            display_text = f"{title} ({file_name})" if title and title != file_name else file_name
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, dup)
            item.setIcon(IconFactory.create_steam_icon() if dup.get('workshop_id') else IconFactory.create_folder_icon())
            self.list_widget.addItem(item)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        self.setStyleSheet(parent.styleSheet() if parent else "")

    def on_item_clicked(self, item):
        dup = item.data(Qt.UserRole)
        if not dup: return
        if dup.get('workshop_id'):
            webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={dup['workshop_id']}")
        else:
            p = dup.get('path')
            if p and os.path.exists(p):
                if sys.platform == 'win32': os.startfile(p)
                else: subprocess.Popen(['xdg-open', p])

# ========== Список с multi-drag, тогглом между секциями и автоскроллом ==========
class ModListWidget(QListWidget):
    listChanged = pyqtSignal()
    crossSectionDrop = pyqtSignal(list, int, int)   # (mod_names, target_section, target_index_in_section)
    dragStarted = pyqtSignal()                       # эмитится при старте drag-and-drop

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMouseTracking(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.scroll_zone_size = 40
        self.scroll_base_speed = 8
        self.autoscroll_timer = QTimer(self)
        self.autoscroll_timer.setInterval(16)
        self.autoscroll_timer.timeout.connect(self.do_autoscroll)
        self._drag_active = False

    def startDrag(self, supportedActions):
        # Сообщаем менеджеру, что начался drag — прячем hover-карточку.
        self._drag_active = True
        self.dragStarted.emit()
        try:
            super().startDrag(supportedActions)
        finally:
            self._drag_active = False

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if event.button() == Qt.RightButton:
            # Если ПКМ пришёлся на уже выделенный элемент при мультивыделении —
            # не даём Qt сбросить выделение, чтобы менеджер мог обработать всю группу.
            if item and item.isSelected() and len(self.selectedItems()) > 1:
                event.accept()
                return
        super().mousePressEvent(event)

    def get_section(self, row):
        if row < 0: return -1
        item = self.item(row)
        if not (item.flags() & Qt.ItemIsSelectable): return -1
        for i in range(row - 1, -1, -1):
            if not (self.item(i).flags() & Qt.ItemIsSelectable):
                text = self.item(i).text()
                if text in ("Включенные моды", "Enabled mods"): return 0
                elif text in ("Выключенные моды", "Disabled mods"): return 1
        return 0

    def _index_in_section(self, row, section):
        header_ru = "Включенные моды" if section == 0 else "Выключенные моды"
        header_en = "Enabled mods" if section == 0 else "Disabled mods"
        start = -1
        for i in range(row - 1, -1, -1):
            t = self.item(i).text()
            if t in (header_ru, header_en):
                start = i; break
        if start == -1: return 0
        count = 0
        for i in range(start + 1, row):
            if self.item(i).flags() & Qt.ItemIsSelectable:
                count += 1
        return count

    def _sort_disabled_section(self):
        """Сортирует элементы секции 'Выключенные' по алфавиту.
        Используется после выключения модов и для блокировки перестановки в секции."""
        header_idx = -1
        for i in range(self.count()):
            item = self.item(i)
            if not (item.flags() & Qt.ItemIsSelectable):
                if item.text() in ("Выключенные моды", "Disabled mods"):
                    header_idx = i
                    break
        if header_idx == -1:
            return
        start = header_idx + 1
        items = []
        for i in range(self.count() - 1, start - 1, -1):
            item = self.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                items.insert(0, self.takeItem(i))
        items.sort(key=lambda it: (it.data(Qt.UserRole + 3) or it.text()).lower())
        for offset, item in enumerate(items):
            self.insertItem(start + offset, item)

    def dragMoveEvent(self, event):
        self._drag_active = True
        if self._is_in_scroll_zone(event.pos()):
            if not self.autoscroll_timer.isActive():
                self.autoscroll_timer.start()
        else:
            self.autoscroll_timer.stop()
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        source_items = self.selectedItems()
        target_item = self.itemAt(event.pos())
        if not source_items or not target_item:
            event.ignore(); return

        target_section = self.get_section(self.row(target_item))
        if target_section == -1:
            event.ignore(); return

        source_section = self.get_section(self.row(source_items[0]))
        all_same = all(self.get_section(self.row(it)) == source_section for it in source_items if it.flags() & Qt.ItemIsSelectable)
        if not all_same:
            event.ignore(); return

        if source_section != target_section:
            mod_names = [it.data(Qt.UserRole + 3) or it.text() for it in source_items if it.flags() & Qt.ItemIsSelectable]
            target_index = self._index_in_section(self.row(target_item), target_section)
            if event.pos().y() > self.visualItemRect(target_item).center().y():
                target_index += 1
            self.crossSectionDrop.emit(mod_names, target_section, target_index)
            event.ignore()
            return

        # Оба элемента в секции "Выключенные" — блокируем изменение порядка.
        # Пересортировка возвращает секцию к исходному алфавитному состоянию.
        if source_section == 1:
            event.ignore()
            self._sort_disabled_section()
            return

        self.autoscroll_timer.stop()
        self._drag_active = False
        super().dropEvent(event)
        self.listChanged.emit()

    def do_autoscroll(self):
        if not self._drag_active:
            self.autoscroll_timer.stop(); return
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        if not self.viewport().rect().contains(pos):
            self.autoscroll_timer.stop(); return
        if not self._is_in_scroll_zone(pos):
            self.autoscroll_timer.stop(); return
        v = self.verticalScrollBar()
        height = self.viewport().height()
        if pos.y() < self.scroll_zone_size:
            normalized = 1.0 - (pos.y() / self.scroll_zone_size); direction = -1
        else:
            normalized = (pos.y() - (height - self.scroll_zone_size)) / self.scroll_zone_size
            direction = 1
        delta = int(self.scroll_base_speed * (0.2 + 0.8 * normalized))
        v.setValue(v.value() + direction * delta)

    def _is_in_scroll_zone(self, pos):
        h = self.viewport().height()
        return (pos.y() < self.scroll_zone_size) or (pos.y() > (h - self.scroll_zone_size))

# ========== Всплывающая карточка мода ==========
class ModHoverCard(QWidget):
    def __init__(self, parent=None):
        # Используем Qt.Tool + FramelessWindowHint + WindowStaysOnTopHint,
        # чтобы карточка получала события Enter/Leave и не забирала фокус.
        super().__init__(parent,
                         Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setFixedWidth(420)
        self.setStyleSheet("ModHoverCard { background: #2a1f15; border: 1px solid #6b5a4a; border-radius: 6px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.image_label = ClickableLabel()
        self.image_label.setFixedHeight(180)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: #1e160e; border: 1px solid #4a3a2a; border-radius: 4px; color: #b09a80;")
        layout.addWidget(self.image_label)

        self.title_label = ClickableLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color: #f0e0c8; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #e8d5b5; font-size: 12px;")
        self.desc_label.setTextFormat(Qt.PlainText)
        layout.addWidget(self.desc_label)

        self.workshop_id = None
        self.image_label.clicked.connect(self._open_workshop)
        self.title_label.clicked.connect(self._open_workshop)

    def set_workshop_id(self, wid):
        self.workshop_id = wid
        cursor = Qt.PointingHandCursor if wid else Qt.ArrowCursor
        self.image_label.setCursor(cursor)
        self.title_label.setCursor(cursor)
        tooltip = "" if not wid else "Открыть страницу в Workshop"
        self.image_label.setToolTip(tooltip)
        self.title_label.setToolTip(tooltip)

    def _open_workshop(self):
        if self.workshop_id:
            webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.workshop_id}")
            # Принудительно скрываем карточку
            self.hide()

    def set_content(self, title, description, pixmap=None, loading=False, no_desc_text="No description."):
        if loading:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("...")
        elif pixmap and not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaledToHeight(180, Qt.SmoothTransformation))
            self.image_label.setText("")
        else:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("")
        self.title_label.setText(title or "")
        desc = strip_bbcode(description or "").strip()
        if not desc: desc = no_desc_text
        if len(desc) > 400: desc = desc[:400] + "…"
        self.desc_label.setText(desc)

    def show_at(self, global_pos):
        screen = QApplication.primaryScreen().availableGeometry()
        x = global_pos.x() + 20
        y = global_pos.y() + 20
        self.adjustSize()
        w, h = self.width(), self.height()
        if x + w > screen.right(): x = global_pos.x() - w - 20
        if y + h > screen.bottom(): y = screen.bottom() - h - 10
        if x < screen.left(): x = screen.left() + 10
        if y < screen.top(): y = screen.top() + 10
        self.move(x, y); self.show()

# ========== Диалог настроек ==========
class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_manager = parent
        s = parent.str
        self.setWindowTitle(s['settings_title'])
        self.setMinimumWidth(480)
        self.result_path = parent.kenshi_path

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.addItem("English", "en")
        idx = self.lang_combo.findData(parent.current_lang)
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
        form.addRow(s['settings_lang'], self.lang_combo)
        layout.addLayout(form)

        hover_group = QGroupBox(s['settings_hover_group'])
        hv_layout = QVBoxLayout(hover_group)
        self.hover_enabled = QCheckBox(s['settings_hover_enabled'])
        self.hover_enabled.setChecked(parent.hover_cards_enabled)
        hv_layout.addWidget(self.hover_enabled)

        delay_row = QHBoxLayout()
        delay_row.addWidget(QLabel(s['settings_hover_delay']))
        self.hover_delay = QSpinBox()
        self.hover_delay.setRange(100, 5000)
        self.hover_delay.setSingleStep(100)
        self.hover_delay.setValue(parent.hover_delay_ms)
        delay_row.addWidget(self.hover_delay)
        delay_row.addStretch()
        hv_layout.addLayout(delay_row)

        hint = QLabel(s['settings_hover_hint'])
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #b09a80; font-size: 11px;")
        hv_layout.addWidget(hint)
        layout.addWidget(hover_group)

        beh_group = QGroupBox(s['settings_behavior_group'])
        beh_layout = QVBoxLayout(beh_group)
        self.close_after_launch = QCheckBox(s['settings_close_after_launch'])
        self.close_after_launch.setChecked(parent.close_after_launch)
        beh_layout.addWidget(self.close_after_launch)
        layout.addWidget(beh_group)

        path_group = QGroupBox(s['settings_kenshi_path_group'])
        p_layout = QVBoxLayout(path_group)
        row = QHBoxLayout()
        row.addWidget(QLabel(f"{s['settings_kenshi_current']}:"))
        self.path_label = QLabel(parent.kenshi_path or s['settings_kenshi_none'])
        self.path_label.setStyleSheet("color: #f0e0c8; font-weight: bold;")
        self.path_label.setWordWrap(True)
        row.addWidget(self.path_label, 1)
        p_layout.addLayout(row)

        btn_change = QPushButton(s['settings_change_path'])
        btn_change.clicked.connect(self.change_path)
        p_layout.addWidget(btn_change)
        layout.addWidget(path_group)

        last_cfg = parent.settings.value("last_cfg_file", "", type=str)
        last_cfg_display = os.path.basename(last_cfg) if last_cfg else s['settings_none']
        info_row = QHBoxLayout()
        info_row.addWidget(QLabel(f"{s['settings_last_cfg']}:"))
        lbl = QLabel(last_cfg_display)
        lbl.setStyleSheet("color: #f0e0c8; font-weight: bold;")
        info_row.addWidget(lbl); info_row.addStretch()
        layout.addLayout(info_row)

        btns = QDialogButtonBox()
        btns.addButton(s['settings_save'], QDialogButtonBox.AcceptRole)
        btns.addButton(s['settings_cancel'], QDialogButtonBox.RejectRole)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setStyleSheet(parent.styleSheet())

    def change_path(self):
        folder = QFileDialog.getExistingDirectory(self, self.parent_manager.str['settings_change_path'])
        if folder:
            self.result_path = folder
            self.path_label.setText(folder)

    def get_values(self):
        return {
            'lang': self.lang_combo.currentData(),
            'hover_enabled': self.hover_enabled.isChecked(),
            'hover_delay': self.hover_delay.value(),
            'close_after_launch': self.close_after_launch.isChecked(),
            'kenshi_path': self.result_path,
        }

# ========== Вспомогательные функции ==========
def read_mod_info(folder_path):
    for f in os.listdir(folder_path):
        if f.lower() in ('info', 'info.xml', 'modinfo.xml') or f.lower().endswith('.info'):
            info_file = os.path.join(folder_path, f)
            try:
                tree = ET.parse(info_file); root = tree.getroot()
                title = root.find('title'); mod_id = root.find('id')
                return {'title': title.text if title is not None else None,
                        'id': mod_id.text if mod_id is not None else None}
            except: continue
    return None

# ========== ГЛАВНОЕ ОКНО ==========
class ModManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("p4vl0-dev", "KenshiSimpleModManager")
        saved_lang = self.settings.value("language", "ru", type=str)
        self.current_lang = saved_lang if saved_lang in LANGUAGES else "ru"
        self.str = LANGUAGES[self.current_lang]

        self.hover_cards_enabled = self.settings.value("hover_cards_enabled", True, type=bool)
        self.hover_delay_ms = self.settings.value("hover_delay_ms", 800, type=int)
        self.close_after_launch = self.settings.value("close_after_launch", False, type=bool)
        saved_path = self.settings.value("kenshi_path", "", type=str)

        self.current_version = get_file_version(sys.argv[0]) or "dev"
        self.update_window_title()
        self.setMinimumSize(750, 700)

        icon_path = self.find_resource("ksmm.ico") or self.find_resource("ksmm.png")
        if icon_path and os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))

        font_path = self.find_resource("Kenshi.ttf", subdir="fonts")
        if font_path and os.path.exists(font_path):
            fid = QFontDatabase.addApplicationFont(font_path)
            if fid != -1:
                fam = QFontDatabase.applicationFontFamilies(fid)[0]
                self.setFont(QFont(fam, 10))

        self.exo_font = None
        exo_path = self.find_resource("Exo2-Bold.ttf", subdir="fonts")
        if exo_path and os.path.exists(exo_path):
            fid = QFontDatabase.addApplicationFont(exo_path)
            if fid != -1:
                fam = QFontDatabase.applicationFontFamilies(fid)[0]
                self.exo_font = QFont(fam, 12, QFont.Bold)

        self.kenshi_path = None
        self.mods_folder = None
        self.workshop_folder = None
        self.mods_cfg_path = None
        self.game_process = None

        self.mod_status = {}
        self.mod_paths = {}
        self.mod_info = {}
        self.mod_deps = {}
        self.workshop_ids = {}
        self.mod_dubles = {}
        self.modified = False
        self.original_enabled_list = []
        self.enabled_list = []
        self.disabled_list = []

        self.workshop_cache = {}
        self.image_cache = {}
        self.network_manager = QNetworkAccessManager(self)

        # Hover-карточка и таймеры
        self.hover_card = ModHoverCard(self)
        self.hover_card.installEventFilter(self)
        self.hover_show_timer = QTimer(self); self.hover_show_timer.setSingleShot(True)
        self.hover_show_timer.timeout.connect(self.show_hover_card_for_current)
        self.hover_hide_timer = QTimer(self); self.hover_hide_timer.setSingleShot(True)
        self.hover_hide_timer.setInterval(4000)   # задержка после ухода мыши с мода
        self.hover_hide_timer.timeout.connect(self._do_hide_hover_card)
        self.hover_current_item = None

        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8); main_layout.setContentsMargins(10, 10, 10, 10)

        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background: #2a1f15; color: #e8d5b5; font-weight: bold; spacing: 0px; }
            QMenuBar::item { padding: 6px 10px; background: transparent; }
            QMenuBar::item:selected { background: #5a4534; }
            QMenu { background: #2a1f15; color: #e8d5b5; border: 1px solid #4a3a2a; }
            QMenu::item:selected { background: #5a4534; }
        """)

        self.file_menu = menubar.addMenu(self.str['menu_file'])
        self.action_load_cfg = QAction(self.str['menu_load_cfg'], self)
        self.action_load_cfg.triggered.connect(self.load_cfg_file)
        self.file_menu.addAction(self.action_load_cfg)

        self.action_backup = QAction(self.str['menu_backup'], self)
        self.action_backup.triggered.connect(self.backup_mods_cfg_manual)
        self.file_menu.addAction(self.action_backup)

        self.file_menu.addSeparator()
        self.action_exit = QAction(self.str['menu_exit'], self)
        self.action_exit.triggered.connect(self.close)
        self.file_menu.addAction(self.action_exit)

        self.view_menu = menubar.addMenu(self.str['menu_view'])
        self.action_refresh = QAction(self.str['menu_refresh'], self)
        self.action_refresh.triggered.connect(self.load_mods_with_confirm)
        self.view_menu.addAction(self.action_refresh)
        self.action_settings = QAction(self.str['menu_settings'], self)
        self.action_settings.triggered.connect(self.show_settings)
        self.view_menu.addAction(self.action_settings)

        self.help_menu = menubar.addMenu(self.str['menu_help'])
        self.action_about = QAction(self.str['menu_about'], self)
        self.action_about.triggered.connect(self.show_about)
        self.help_menu.addAction(self.action_about)

        self.btn_github = QPushButton()
        self.btn_github.setIcon(IconFactory.create_github_icon())
        self.btn_github.setIconSize(QSize(20, 20)); self.btn_github.setFlat(True)
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.clicked.connect(lambda: webbrowser.open(self.str['github_url']))
        self.btn_github.setStyleSheet("QPushButton{background:transparent;border:none;padding:4px 6px;} QPushButton:hover{background:#5a4534;border-radius:4px;}")
        self.btn_github.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.btn_lang = QPushButton(self.str['btn_lang'])
        self.btn_lang.setObjectName("btn_lang")
        self.btn_lang.clicked.connect(self.toggle_language)
        self.btn_lang.setStyleSheet("QPushButton#btn_lang{background:transparent;border:none;padding:6px 10px;color:#e8d5b5;font-weight:bold;font-size:13px;} QPushButton#btn_lang:hover{background:#5a4534;}")
        self.btn_lang.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        corner_widget = QWidget(); corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 0); corner_layout.setSpacing(2)
        corner_layout.addWidget(self.btn_github); corner_layout.addWidget(self.btn_lang)
        self.menuBar().setCornerWidget(corner_widget, Qt.TopRightCorner)

        search_layout = QHBoxLayout(); search_layout.setSpacing(5)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.str['search_placeholder'])
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setStyleSheet("QLineEdit{background:#2a1f15;color:#e8d5b5;border:1px solid #4a3a2a;border-radius:4px;padding:4px 8px;font-size:13px;}")
        search_layout.addWidget(self.search_input)

        self.btn_search_up = QPushButton("▲"); self.btn_search_up.setFixedSize(24, 24)
        self.btn_search_up.clicked.connect(self.search_prev); self.btn_search_up.setStyleSheet(self.button_style())
        search_layout.addWidget(self.btn_search_up)

        self.btn_search_down = QPushButton("▼"); self.btn_search_down.setFixedSize(24, 24)
        self.btn_search_down.clicked.connect(self.search_next); self.btn_search_down.setStyleSheet(self.button_style())
        search_layout.addWidget(self.btn_search_down)

        main_layout.insertLayout(1, search_layout)

        self.list_widget = ModListWidget(self)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.delegate = ModItemDelegate(self)
        self.list_widget.setItemDelegate(self.delegate)
        self.list_widget.listChanged.connect(self.on_list_changed)
        self.list_widget.crossSectionDrop.connect(self.on_cross_section_drop)
        self.list_widget.dragStarted.connect(self.on_drag_started)
        self.list_widget.currentItemChanged.connect(self.on_current_mod_changed)
        self.list_widget.setStyleSheet("""
            QListWidget { background: #1e160e; border: 1px solid #4a3a2a; border-radius: 6px;
                          outline: none; font-weight: bold; font-size: 13px; color: #e8d5b5; }
            QListWidget::item { border-bottom: 1px solid #3a2c1e; padding: 6px 10px; background: #2a1f15; }
            QListWidget::item:selected { background: #5a4534; }
            QScrollBar:vertical { background: #1e160e; width: 18px; border-radius: 9px; }
            QScrollBar::handle:vertical { background: #5a4534; border-radius: 9px; min-height: 30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self.list_widget.viewport().installEventFilter(self)
        main_layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout(); btn_layout.setSpacing(10); btn_layout.addStretch()
        self.btn_save = QPushButton(self.str['btn_save'])
        self.btn_save.clicked.connect(self.save_mods); self.btn_save.setEnabled(False)
        self.btn_save.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        btn_layout.addWidget(self.btn_save)

        self.btn_launch = QPushButton(self.str['btn_launch'])
        self.btn_launch.clicked.connect(self.launch_game)
        self.btn_launch.setStyleSheet(self.button_style())
        self.btn_launch.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        btn_layout.addWidget(self.btn_launch)

        btn_layout.addStretch(); main_layout.addLayout(btn_layout)

        self.statusBar().setStyleSheet("QStatusBar{background:#1e160e;color:#b09a80;border-top:1px solid #3a2c1e;padding:4px;font-weight:bold;}")
        self.statusBar().showMessage(self.str['status_init'])

        self.setStyleSheet("""
            QMainWindow { background: #1e160e; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5a4534, stop:1 #3c2f22);
                border: 1px solid #6b5a4a; border-radius: 4px; padding: 6px 14px;
                color: #e8d5b5; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6b5a4a, stop:1 #4a3a2a); }
            QPushButton:pressed { background: #2a1f15; }
            QToolTip { background: #2a1f15; color: #e8d5b5; border: 1px solid #4a3a2a; padding: 4px; }
        """)

        if saved_path and os.path.exists(os.path.join(saved_path, "data", "mods.cfg")):
            self.kenshi_path = saved_path
            self.update_paths(saved_path)
            self.statusBar().showMessage(self.str['status_found_kenshi'].format(saved_path))
        else:
            self.auto_detect_paths()
            if self.kenshi_path:
                self.settings.setValue("kenshi_path", self.kenshi_path)

        if self.mods_cfg_path and os.path.exists(self.mods_cfg_path):
            self.load_mods(ask_confirmation=False)
        else:
            self.statusBar().showMessage(self.str['status_paths_not_set'])

        QTimer.singleShot(1500, self.check_for_updates)

    def update_window_title(self):
        last_cfg = self.settings.value("last_cfg_file", "", type=str)
        suffix = f"  —  {os.path.basename(last_cfg)}" if last_cfg else ""
        self.setWindowTitle(f"{self.str['window_title']} v{self.current_version}{suffix}")

    def show_settings(self):
        self.hide_hover_card()
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            self.settings.setValue("language", vals['lang'])
            self.settings.setValue("hover_cards_enabled", vals['hover_enabled'])
            self.settings.setValue("hover_delay_ms", vals['hover_delay'])
            self.settings.setValue("close_after_launch", vals['close_after_launch'])

            path_changed = False
            new_path = vals['kenshi_path']
            if new_path and new_path != self.kenshi_path and os.path.exists(os.path.join(new_path, "data", "mods.cfg")):
                self.kenshi_path = new_path
                self.settings.setValue("kenshi_path", new_path)
                self.update_paths(new_path)
                path_changed = True

            self.current_lang = vals['lang']
            self.str = LANGUAGES[self.current_lang]
            self.hover_cards_enabled = vals['hover_enabled']
            self.hover_delay_ms = vals['hover_delay']
            self.close_after_launch = vals['close_after_launch']

            self.update_ui_texts()
            if path_changed:
                self.load_mods(ask_confirmation=False)
            else:
                self.build_list(self.enabled_list, self.disabled_list)

            if not self.hover_cards_enabled:
                self.hide_hover_card()

    def toggle_language(self):
        self.current_lang = 'en' if self.current_lang == 'ru' else 'ru'
        self.settings.setValue("language", self.current_lang)
        self.str = LANGUAGES[self.current_lang]
        self.update_ui_texts()
        self.build_list(self.enabled_list, self.disabled_list)

    def update_ui_texts(self):
        self.update_window_title()
        self.file_menu.setTitle(self.str['menu_file'])
        self.action_load_cfg.setText(self.str['menu_load_cfg'])
        self.action_backup.setText(self.str['menu_backup'])
        self.action_exit.setText(self.str['menu_exit'])
        self.view_menu.setTitle(self.str['menu_view'])
        self.action_refresh.setText(self.str['menu_refresh'])
        self.action_settings.setText(self.str['menu_settings'])
        self.help_menu.setTitle(self.str['menu_help'])
        self.action_about.setText(self.str['menu_about'])
        self.btn_save.setText(self.str['btn_save'])
        self.btn_launch.setText(self.str['btn_launch'])
        self.btn_lang.setText(self.str['btn_lang'])
        self.search_input.setPlaceholderText(self.str['search_placeholder'])
        self.delegate.set_tooltip_text(self.str['tooltip_workshop'])
        self.delegate.tooltip_duplicate = self.str['tooltip_duplicate']
        self.delegate.tooltip_folder = self.str['tooltip_folder']
        self.check_if_modified()

    def show_about(self):
        about_text = f"Kenshi Simple Mod Manager v{self.current_version}\n\n{self.str['about_text']}"
        QMessageBox.about(self, self.str['menu_about'], about_text)

    def on_search(self, text):
        first_match_row = -1
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                item.setData(Qt.UserRole + 1, False)
                mn = item.data(Qt.UserRole + 3) or item.text()
                conflicts = self.check_dependencies([m for m, s in self.mod_status.items() if s])
                item.setBackground(QBrush(QColor(180, 150, 50) if mn in conflicts else Qt.transparent))
        if text:
            tl = text.lower()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.flags() & Qt.ItemIsSelectable:
                    title = item.data(Qt.UserRole + 4) or ""
                    if tl in item.text().lower() or tl in title.lower():
                        item.setData(Qt.UserRole + 1, True)
                        if first_match_row == -1: first_match_row = i
        self.list_widget.viewport().update()
        if first_match_row != -1:
            self.list_widget.scrollToItem(self.list_widget.item(first_match_row), QAbstractItemView.PositionAtCenter)
            self.list_widget.setCurrentRow(first_match_row)

    def search_next(self):
        if not self.search_input.text(): return
        text = self.search_input.text().lower()
        start = self.list_widget.currentRow() + 1 if self.list_widget.currentRow() >= 0 else 0
        for i in range(start, self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i); return
        for i in range(0, self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i); return

    def search_prev(self):
        if not self.search_input.text(): return
        text = self.search_input.text().lower()
        start = self.list_widget.currentRow() - 1 if self.list_widget.currentRow() >= 0 else self.list_widget.count() - 1
        for i in range(start, -1, -1):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i); return
        for i in range(self.list_widget.count() - 1, -1, -1):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i); return

    def show_duplicate_dialog(self, mod_name):
        dups = self.mod_dubles.get(mod_name, [])
        if not dups: return
        DuplicateDialog(mod_name, dups, self).exec_()

    def find_resource(self, filename, subdir=""):
        if getattr(sys, 'frozen', False): base = sys._MEIPASS
        else: base = os.path.dirname(os.path.abspath(__file__))
        candidates = []
        if subdir: candidates.append(os.path.join(base, subdir, filename))
        candidates.append(os.path.join(base, filename))
        exe_base = os.path.dirname(os.path.abspath(sys.argv[0]))
        if subdir: candidates.append(os.path.join(exe_base, subdir, filename))
        candidates.append(os.path.join(exe_base, filename))
        for path in candidates:
            if os.path.exists(path): return path
        return None

    def auto_detect_paths(self):
        self.kenshi_path = self.find_kenshi_path()
        if self.kenshi_path:
            self.kenshi_path = os.path.normpath(os.path.abspath(self.kenshi_path))
            self.update_paths(self.kenshi_path)
            self.statusBar().showMessage(self.str['status_found_kenshi'].format(self.kenshi_path))
        else:
            self.statusBar().showMessage(self.str['status_not_found_kenshi'])

    def find_game_exe(self):
        if not self.kenshi_path: return None
        for name in ("kenshi_x64.exe", "kenshi.exe", "Kenshi_x64.exe", "Kenshi.exe"):
            c = os.path.join(self.kenshi_path, name)
            if os.path.exists(c): return c
        return None

    def find_kenshi_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            sp = winreg.QueryValueEx(key, "InstallPath")[0]; winreg.CloseKey(key)
            cand = os.path.join(sp, "steamapps", "common", "Kenshi")
            if os.path.exists(os.path.join(cand, "data", "mods.cfg")): return os.path.abspath(cand)
        except: pass
        for d in [chr(x)+":" for x in range(ord('C'), ord('Z')+1)]:
            for base in [os.path.join(d, "SteamLibrary", "steamapps", "common", "Kenshi"),
                         os.path.join(d, "Program Files (x86)", "Steam", "steamapps", "common", "Kenshi"),
                         os.path.join(d, "Program Files", "Steam", "steamapps", "common", "Kenshi")]:
                if os.path.exists(os.path.join(base, "data", "mods.cfg")): return os.path.abspath(base)
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.exists(os.path.join(exe_dir, "data", "mods.cfg")): return os.path.abspath(exe_dir)
        parent = os.path.dirname(exe_dir)
        if os.path.exists(os.path.join(parent, "data", "mods.cfg")): return os.path.abspath(parent)
        return None

    def update_paths(self, kenshi_path):
        self.kenshi_path = kenshi_path
        self.mods_folder = os.path.join(kenshi_path, "mods")
        self.workshop_folder = self.find_workshop_path(kenshi_path)
        self.mods_cfg_path = os.path.join(kenshi_path, "data", "mods.cfg")

    def find_workshop_path(self, kenshi_path):
        steamapps = os.path.dirname(kenshi_path)
        if os.path.basename(steamapps) != "steamapps": steamapps = os.path.dirname(steamapps)
        cand = os.path.join(steamapps, "workshop", "content", "233860")
        if os.path.exists(cand): return cand
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            sp = winreg.QueryValueEx(key, "InstallPath")[0]; winreg.CloseKey(key)
            cand = os.path.join(sp, "steamapps", "workshop", "content", "233860")
            if os.path.exists(cand): return cand
        except: pass
        for d in [chr(x)+":" for x in range(ord('C'), ord('Z')+1)]:
            for p in [os.path.join(d, "SteamLibrary", "steamapps", "workshop", "content", "233860"),
                      os.path.join(d, "Program Files (x86)", "Steam", "steamapps", "workshop", "content", "233860"),
                      os.path.join(d, "Program Files", "Steam", "steamapps", "workshop", "content", "233860")]:
                if os.path.exists(p): return p
        return None

    def has_mod_file(self, folder_path):
        for root, _, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(".mod"): return True
        return False

    def get_mod_name_from_folder(self, folder_path):
        for root, _, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(".mod"): return os.path.splitext(f)[0]
        return None

    def load_mods_with_confirm(self):
        if self._question_box(self.str['confirm_title'], self.str['question_confirm_refresh']):
            self.load_mods(ask_confirmation=False)

    def load_mods(self, ask_confirmation=False):
        if ask_confirmation:
            if not self._question_box(self.str['confirm_title'], self.str['question_confirm_refresh']):
                return
        if not self.mods_folder or not os.path.exists(self.mods_folder):
            QMessageBox.warning(self, self.str['error_title'], self.str['error_mods_folder']); return

        enabled_names = []
        if os.path.exists(self.mods_cfg_path):
            try:
                with open(self.mods_cfg_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        n = line.strip()
                        if n:
                            if n.lower().endswith('.mod'): n = n[:-4]
                            enabled_names.append(n)
            except Exception as e:
                QMessageBox.critical(self, self.str['error_title'], self.str['error_read_cfg'].format(e)); return

        all_mods_raw = {}
        if os.path.exists(self.mods_folder):
            for mod_dir in os.listdir(self.mods_folder):
                fp = os.path.join(self.mods_folder, mod_dir)
                if os.path.isdir(fp) and self.has_mod_file(fp):
                    name = self.get_mod_name_from_folder(fp)
                    if name:
                        all_mods_raw.setdefault(name, []).append({'path': fp, 'workshop_id': None, 'info': read_mod_info(fp)})
        if self.workshop_folder and os.path.exists(self.workshop_folder):
            for mod_id_dir in os.listdir(self.workshop_folder):
                fp = os.path.join(self.workshop_folder, mod_id_dir)
                if os.path.isdir(fp) and self.has_mod_file(fp):
                    name = self.get_mod_name_from_folder(fp)
                    if name:
                        all_mods_raw.setdefault(name, []).append({'path': fp, 'workshop_id': mod_id_dir, 'info': read_mod_info(fp)})

        if not all_mods_raw:
            QMessageBox.warning(self, self.str['warning_title'], self.str['warning_no_mods'])
            self.list_widget.clear()
            self.mod_status = {}; self.mod_paths = {}; self.mod_info = {}
            self.mod_deps = {}; self.workshop_ids = {}; self.mod_dubles = {}
            return

        self.mod_paths = {}; self.mod_info = {}; self.mod_dubles = {}
        self.workshop_ids = {}; self.mod_deps = {}
        for base_name, items in all_mods_raw.items():
            if len(items) > 1: self.mod_dubles[base_name] = items
            rep = items[0]
            self.mod_paths[base_name] = rep['path']
            self.mod_info[base_name] = rep['info']
            if rep['workshop_id']: self.workshop_ids[base_name] = rep['workshop_id']

        self.mod_status = {m: False for m in self.mod_paths}
        missing = []
        for n in enabled_names:
            if n in self.mod_status: self.mod_status[n] = True
            else: missing.append(n)
        if missing:
            QMessageBox.warning(self, self.str['warning_title'],
                                self.str['warning_missing_mods'].format(', '.join(missing)))

        enabled_list = [n for n in enabled_names if n in self.mod_status and self.mod_status[n]]
        for m, s in self.mod_status.items():
            if s and m not in enabled_list: enabled_list.append(m)
        disabled_list = sorted([m for m, s in self.mod_status.items() if not s])

        self.enabled_list = enabled_list
        self.disabled_list = disabled_list
        self.original_enabled_list = enabled_list[:]
        self.build_list(enabled_list, disabled_list)
        self.modified = False
        self.update_save_button()
        self.statusBar().showMessage(
            self.str['status_loaded_mods'].format(len(enabled_list) + len(disabled_list),
                                                  len(enabled_list), len(disabled_list)))

    def build_list(self, enabled_list, disabled_list):
        self.list_widget.clear()
        conflicts = self.check_dependencies(enabled_list)

        def create_item(mod_name, is_enabled):
            info = self.mod_info.get(mod_name)
            title = info.get('title') if info else None
            item = QListWidgetItem(mod_name)
            item.setData(Qt.UserRole + 3, mod_name)
            item.setData(Qt.UserRole + 4, title if title else "")
            item.setIcon(IconFactory.create_check_icon() if is_enabled else IconFactory.create_cross_icon())
            wid = self.workshop_ids.get(mod_name, "")
            item.setData(Qt.UserRole, wid)
            item.setData(Qt.UserRole + 2, mod_name in self.mod_dubles)
            if mod_name in conflicts:
                item.setBackground(QBrush(QColor(180, 150, 50)))
                item.setData(Qt.UserRole + 5, conflicts[mod_name])
            else:
                item.setBackground(QBrush(Qt.transparent))
                item.setData(Qt.UserRole + 5, "")
            item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled)
            return item

        header_enabled = QListWidgetItem(self.str['header_enabled'])
        header_enabled.setFlags(header_enabled.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled)
        header_enabled.setForeground(QColor("#f0e0c8")); header_enabled.setBackground(QBrush(QColor("#3a2c1e")))
        header_enabled.setTextAlignment(Qt.AlignCenter)
        header_enabled.setFont(self.exo_font if self.exo_font else QFont(self.font().family(), 12, QFont.Bold))
        self.list_widget.addItem(header_enabled)
        for mod in enabled_list: self.list_widget.addItem(create_item(mod, True))

        header_disabled = QListWidgetItem(self.str['header_disabled'])
        header_disabled.setFlags(header_disabled.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled)
        header_disabled.setForeground(QColor("#f0e0c8")); header_disabled.setBackground(QBrush(QColor("#3a2c1e")))
        header_disabled.setTextAlignment(Qt.AlignCenter)
        header_disabled.setFont(self.exo_font if self.exo_font else QFont(self.font().family(), 12, QFont.Bold))
        self.list_widget.addItem(header_disabled)
        for mod in disabled_list: self.list_widget.addItem(create_item(mod, False))

    def check_dependencies(self, enabled_list):
        errors = {}
        index_map = {mod: i for i, mod in enumerate(enabled_list)}
        for mod_name in enabled_list:
            for dep in self.mod_deps.get(mod_name, []):
                if dep not in index_map:
                    errors[mod_name] = f"Отсутствует зависимость: {dep}"
                elif index_map[dep] >= index_map[mod_name]:
                    errors[mod_name] = f"Неверный порядок: {dep} должен загружаться раньше {mod_name}"
        return errors

    def update_conflict_highlights(self):
        enabled_list = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mn = item.data(Qt.UserRole + 3) or item.text()
                if self.mod_status.get(mn, False): enabled_list.append(mn)
        conflicts = self.check_dependencies(enabled_list)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mn = item.data(Qt.UserRole + 3) or item.text()
                if mn in conflicts:
                    item.setBackground(QBrush(QColor(180, 150, 50)))
                    item.setData(Qt.UserRole + 5, conflicts[mn])
                else:
                    item.setBackground(QBrush(Qt.transparent))
                    item.setData(Qt.UserRole + 5, "")

    def check_if_modified(self):
        current = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mn = item.data(Qt.UserRole + 3) or item.text()
                if self.mod_status.get(mn, False): current.append(mn)
        self.modified = (current != self.original_enabled_list)
        self.update_save_button()

    def show_save_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.str['confirm_title']); msg.setText(self.str['save_dialog_text'])
        btn_save = msg.addButton(self.str['save_btn_save'], QMessageBox.AcceptRole)
        btn_backup = msg.addButton(self.str['save_btn_backup'], QMessageBox.ActionRole)
        msg.addButton(self.str['save_btn_cancel'], QMessageBox.RejectRole)
        msg.setDefaultButton(btn_save); msg.exec_()
        clicked = msg.clickedButton()
        if clicked == btn_save: return 'save'
        elif clicked == btn_backup: return 'backup'
        return 'cancel'

    def save_mods(self):
        if not self.mods_cfg_path:
            QMessageBox.warning(self, self.str['error_title'], "Путь к mods.cfg не задан."); return
        if self.mod_dubles:
            if not self._question_box(self.str['confirm_title'], self.str['question_duplicates_save']): return
        if self.modified:
            action = self.show_save_dialog()
            if action == 'cancel': return
            if action == 'backup':
                if not self.backup_mods_cfg_manual(show_success=False): return

        enabled_in_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mn = item.data(Qt.UserRole + 3) or item.text()
                if self.mod_status.get(mn, False): enabled_in_order.append(mn)
        try:
            with open(self.mods_cfg_path, 'w', encoding='utf-8') as f:
                for mn in enabled_in_order: f.write(mn + '.mod\n')
            self.statusBar().showMessage(self.str['status_saved_mods'].format(len(enabled_in_order), self.mods_cfg_path))
            self.original_enabled_list = enabled_in_order[:]
            self.modified = False; self.update_save_button()
            QMessageBox.information(self, self.str['info_title'], self.str['info_save_success'])
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'], self.str['error_save_cfg'].format(e))

    def load_cfg_file(self):
        self.hide_hover_card()
        file_path, _ = QFileDialog.getOpenFileName(self, self.str['menu_load_cfg'], "", "CFG Files (*.cfg);;All Files (*)")
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip()]
            mod_names = []
            for line in lines:
                n = line.strip()
                if n.lower().endswith('.mod'): n = n[:-4]
                mod_names.append(n)

            for mod in self.mod_status.keys(): self.mod_status[mod] = False
            for n in mod_names:
                if n in self.mod_status: self.mod_status[n] = True

            enabled_list = [m for m, s in self.mod_status.items() if s]
            disabled_list = [m for m, s in self.mod_status.items() if not s]
            enabled_ordered = [m for m in mod_names if m in self.mod_status and self.mod_status[m]]
            for m in enabled_list:
                if m not in enabled_ordered: enabled_ordered.append(m)
            disabled_ordered = sorted(disabled_list)
            self.enabled_list = enabled_ordered
            self.disabled_list = disabled_ordered
            self.build_list(enabled_ordered, disabled_ordered)
            self.modified = True; self.update_save_button()

            self.settings.setValue("last_cfg_file", file_path)
            self.update_window_title()

            self.statusBar().showMessage(self.str['status_cfg_loaded'].format(file_path))
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'], f"Не удалось загрузить CFG:\n{e}")

    def backup_mods_cfg_manual(self, show_success=True):
        self.hide_hover_card()
        if not self.mods_cfg_path or not os.path.exists(self.mods_cfg_path):
            QMessageBox.warning(self, self.str['error_title'], "Файл mods.cfg не найден."); return False
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.str['backup_choose_title'],
            os.path.join(os.path.dirname(self.mods_cfg_path), "mods.cfg"),
            self.str['backup_filter'])
        if not file_path: return False
        try:
            import shutil
            shutil.copy2(self.mods_cfg_path, file_path)
            if show_success:
                self.statusBar().showMessage(self.str['status_backup_created'].format(file_path))
                QMessageBox.information(self, self.str['info_title'], f"Файл сохранён:\n{file_path}")
            self.settings.setValue("last_cfg_file", file_path)
            self.update_window_title()
            return True
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'], f"Не удалось сохранить файл:\n{e}")
            self.statusBar().showMessage(self.str['status_backup_failed'].format(e))
            return False

    def update_save_button(self):
        if self.modified:
            self.btn_save.setEnabled(True)
            self.btn_save.setStyleSheet(self.button_style() + """
                QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a3a2a, stop:1 #5a2a1a);
                              border-color: #aa5a4a; }
                QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9a4a3a, stop:1 #6a3a2a); }
            """)
        else:
            self.btn_save.setEnabled(False)
            self.btn_save.setStyleSheet(self.button_style() + """
                QPushButton { background: #3a2f22; color: #7a6a5a; border: 1px solid #4a3a2a; }
            """)

    def on_list_changed(self):
        self.check_if_modified()

    def on_cross_section_drop(self, mod_names, target_section, target_index):
        for mn in mod_names:
            if mn in self.enabled_list: self.enabled_list.remove(mn)
            if mn in self.disabled_list: self.disabled_list.remove(mn)

        for mn in mod_names:
            self.mod_status[mn] = (target_section == 0)

        if target_section == 0:
            # В секции "Включённые" позиция drop учитывается.
            for offset, mn in enumerate(mod_names):
                pos = min(target_index + offset, len(self.enabled_list))
                self.enabled_list.insert(pos, mn)
        else:
            # В секции "Выключенные" порядок всегда алфавитный —
            # позиция drop игнорируется.
            for mn in mod_names:
                self.disabled_list.append(mn)
            self.disabled_list.sort(key=str.lower)

        self.build_list(self.enabled_list, self.disabled_list)
        self.check_if_modified()
        enabled_count = sum(self.mod_status.values())
        word = self.str['mod_status_enabled'] if target_section == 0 else self.str['mod_status_disabled']
        self.statusBar().showMessage(f"{len(mod_names)} × {word}  ({enabled_count})")

    def on_drag_started(self):
        """При старте drag-and-drop прячем hover-карточку."""
        self.hide_hover_card()

    def on_current_mod_changed(self, current, previous):
        if current and (current.flags() & Qt.ItemIsSelectable):
            mn = current.data(Qt.UserRole + 3) or current.text()
            if mn in self.workshop_ids:
                self.statusBar().showMessage(self.str['status_mod_selected_workshop'].format(mn))
            else:
                self.statusBar().showMessage(self.str['status_mod_selected_local'].format(mn))

    def launch_game(self):
        self.hide_hover_card()
        if not self.kenshi_path:
            QMessageBox.warning(self, self.str['error_title'], "Путь к Kenshi не задан."); return
        game_exe = self.find_game_exe()
        if not game_exe:
            QMessageBox.warning(self, self.str['error_title'],
                                f"Не найден исполняемый файл игры в папке:\n{self.kenshi_path}"); return
        try:
            game_folder = os.path.dirname(game_exe)
            clean_env = os.environ.copy()
            if hasattr(sys, '_MEIPASS'):
                if 'PATH_ORIG' in clean_env: clean_env['PATH'] = clean_env['PATH_ORIG']
                clean_env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
                clean_env.pop('PYIDIE_VERBOSE', None)

            steam_exe = os.path.abspath(os.path.join(game_folder, "..", "..", "..", "steam.exe"))
            if not os.path.exists(steam_exe):
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
                    sp = winreg.QueryValueEx(key, "InstallPath")[0]; winreg.CloseKey(key)
                    steam_exe = os.path.join(sp, "steam.exe")
                except: steam_exe = None

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            if steam_exe and os.path.exists(steam_exe):
                self.game_process = subprocess.Popen(
                    [steam_exe, "-applaunch", "233860"], cwd=game_folder, env=clean_env,
                    startupinfo=startupinfo, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.game_process = subprocess.Popen(
                    [game_exe], cwd=game_folder, env=clean_env,
                    startupinfo=startupinfo, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            self.statusBar().showMessage(self.str['status_game_launched'])
            if self.close_after_launch:
                self.close()
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'],
                                 self.str['error_launch_game'].format(e) + f"\n\nПуть: {game_exe}")

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item and (item.flags() & Qt.ItemIsSelectable):
            # Собираем все выделенные моды (исключая заголовки секций)
            selected = [it for it in self.list_widget.selectedItems()
                        if it.flags() & Qt.ItemIsSelectable]
            # Сортируем по визуальному порядку в списке
            selected.sort(key=lambda it: self.list_widget.row(it))

            # Если выделено несколько модов и клик пришёлся по одному из них —
            # переключаем всю группу разом.
            if len(selected) > 1 and item in selected:
                mod_names = [it.data(Qt.UserRole + 3) or it.text() for it in selected]
                self.toggle_mods(mod_names)
            else:
                mn = item.data(Qt.UserRole + 3) or item.text()
                self.toggle_mod(mn)
            return

        menu = QMenu()
        a1 = menu.addAction(self.str['menu_refresh']); a1.triggered.connect(self.load_mods_with_confirm)
        menu.addSeparator()
        a2 = menu.addAction(self.str['menu_settings']); a2.triggered.connect(self.show_settings)
        a3 = menu.addAction(self.str['btn_launch']); a3.triggered.connect(self.launch_game)
        menu.exec_(self.list_widget.mapToGlobal(pos))

    def _enabled_section_insert_pos(self):
        """Позиция вставки в конец секции 'Включённые' (перед заголовком 'Выключенные')."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not (item.flags() & Qt.ItemIsSelectable):
                if item.text() in ("Выключенные моды", "Disabled mods"):
                    return i
        return self.list_widget.count()

    def _disabled_section_insert_pos(self, mod_name):
        """Позиция вставки в секцию 'Выключенные' с сохранением алфавитного порядка (для одиночного мода)."""
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() in ("Выключенные моды", "Disabled mods"):
                j = i + 1
                while j < self.list_widget.count():
                    ci = self.list_widget.item(j)
                    if not (ci.flags() & Qt.ItemIsSelectable):
                        return j
                    cm = ci.data(Qt.UserRole + 3) or ci.text()
                    if cm.lower() > mod_name.lower():
                        return j
                    j += 1
                return j
        return self.list_widget.count()

    def toggle_mods(self, mod_names):
        """Переключает один или несколько модов разом.
        Новое состояние определяется по первому моду списка:
        если он был включён — выключаем все, если выключен — включаем все."""
        if not mod_names:
            return
        self.hide_hover_card()

        first = mod_names[0]
        new_status = not self.mod_status.get(first, False)
        names_set = set(mod_names)

        # Обновляем статусы
        for mn in mod_names:
            self.mod_status[mn] = new_status

        # Собираем и удаляем элементы (идём с конца, чтобы не сбить индексы)
        items_to_move = []
        for i in range(self.list_widget.count() - 1, -1, -1):
            item = self.list_widget.item(i)
            if not (item.flags() & Qt.ItemIsSelectable):
                continue
            mn = item.data(Qt.UserRole + 3) or item.text()
            if mn in names_set:
                items_to_move.insert(0, self.list_widget.takeItem(i))

        # Обновляем иконки
        for item in items_to_move:
            item.setIcon(IconFactory.create_check_icon() if new_status
                         else IconFactory.create_cross_icon())

        if new_status:
            # Включение: добавляем в конец секции "Включённые", сохраняя порядок группы.
            insert_pos = self._enabled_section_insert_pos()
            for item in items_to_move:
                self.list_widget.insertItem(insert_pos, item)
                insert_pos += 1
        else:
            # Выключение: добавляем в конец списка и сортируем секцию "Выключенные"
            # по алфавиту. Порядок, в котором моды выключались, значения не имеет.
            for item in items_to_move:
                self.list_widget.addItem(item)
            self.list_widget._sort_disabled_section()

        self.update_conflict_highlights()
        self.check_if_modified()

        enabled_count = sum(self.mod_status.values())
        status_word = self.str['mod_status_enabled'] if new_status else self.str['mod_status_disabled']

        if len(mod_names) == 1:
            self.statusBar().showMessage(
                self.str['status_mod_toggled'].format(mod_names[0], status_word, enabled_count))
        else:
            self.statusBar().showMessage(
                f"{len(mod_names)} × {status_word}  ({enabled_count})")

    def toggle_mod(self, mod_name):
        """Совместимость: одиночное переключение = батч из одного мода."""
        self.toggle_mods([mod_name])

    def button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5a4534, stop:1 #3c2f22);
                border: 1px solid #6b5a4a; border-radius: 4px; padding: 6px 14px;
                color: #e8d5b5; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6b5a4a, stop:1 #4a3a2a); }
            QPushButton:pressed { background: #2a1f15; }
        """

    def _question_box(self, title, text):
        self.hide_hover_card()
        msg = QMessageBox(self)
        msg.setWindowTitle(title); msg.setText(text)
        btn_yes = msg.addButton(self.str['yes'], QMessageBox.YesRole)
        msg.addButton(self.str['no'], QMessageBox.NoRole)
        msg.setDefaultButton(btn_yes); msg.exec_()
        return msg.clickedButton() == btn_yes

    # ========== HOVER-КАРТОЧКА ==========
    def eventFilter(self, obj, event):
        if obj is self.list_widget.viewport():
            if event.type() == QEvent.MouseMove:
                self._on_viewport_mouse_move(event.pos())
            elif event.type() == QEvent.Leave:
                if self.hover_card.isVisible():
                    self._schedule_hide_hover_card()
        elif obj is self.hover_card:
            if event.type() == QEvent.Enter:
                self._cancel_hide_hover_card()
            elif event.type() == QEvent.Leave:
                self._schedule_hide_hover_card()
        return super().eventFilter(obj, event)

    def _on_viewport_mouse_move(self, pos):
        if not self.hover_cards_enabled:
            self.hide_hover_card(); return

        # Во время drag-and-drop карточку не показываем
        if getattr(self.list_widget, '_drag_active', False):
            self.hide_hover_card(); return

        # Не показываем карточку, если окно менеджера неактивно
        if not self.isActiveWindow():
            self.hide_hover_card(); return

        item = self.list_widget.itemAt(pos)
        over_text = False
        if item and (item.flags() & Qt.ItemIsSelectable):
            rect = self.list_widget.visualItemRect(item)
            icon_size = 20; dup_icon_size = 16
            right_shift = icon_size + 5
            if item.data(Qt.UserRole + 2): right_shift += dup_icon_size + 5
            text_right = rect.right() - right_shift
            if pos.x() <= text_right:
                over_text = True

        if over_text:
            self._cancel_hide_hover_card()
            if self.hover_current_item is item:
                return
            self.hover_current_item = item
            self.hover_card.hide()
            self.hover_show_timer.start(self.hover_delay_ms)
        else:
            # Мышь ушла с мода — планируем скрытие, но даём время дойти до карточки
            if self.hover_card.isVisible():
                self._schedule_hide_hover_card()
            else:
                self.hover_show_timer.stop()

    def _schedule_hide_hover_card(self):
        self.hover_show_timer.stop()
        self.hover_hide_timer.start()  # интервал задан в __init__ (2000 мс)

    def _cancel_hide_hover_card(self):
        self.hover_hide_timer.stop()

    def hide_hover_card(self):
        self.hover_show_timer.stop()
        self.hover_hide_timer.stop()
        self.hover_current_item = None
        self.hover_card.hide()

    def _do_hide_hover_card(self):
        self.hover_current_item = None
        self.hover_card.hide()

    def show_hover_card_for_current(self):
        item = self.hover_current_item
        if not item or not self.hover_cards_enabled: return

        # Во время drag-and-drop карточку не показываем
        if getattr(self.list_widget, '_drag_active', False):
            return

        # Проверяем, что курсор всё ещё над тем же модом и окно активно
        if not self.isActiveWindow():
            return
        vp_pos = self.list_widget.viewport().mapFromGlobal(QCursor.pos())
        if not self.list_widget.viewport().rect().contains(vp_pos):
            return
        cur_item = self.list_widget.itemAt(vp_pos)
        if cur_item is not item:
            return

        mod_name = item.data(Qt.UserRole + 3) or item.text()
        wid = item.data(Qt.UserRole)
        title = item.data(Qt.UserRole + 4) or mod_name
        conflict = item.data(Qt.UserRole + 5) or ""

        cursor_pos = QCursor.pos()
        self.hover_card.set_workshop_id(wid or None)

        if wid:
            self.hover_card.set_content(title, "", None, loading=True)
            self.hover_card.show_at(cursor_pos)

            def on_details(info):
                if info is None:
                    info = {'title': title, 'description': conflict, 'image_url': ''}
                t = info.get('title') or title
                d = info.get('description') or ''
                if conflict:
                    d = (d + '\n\n⚠ ' + conflict) if d else ('⚠ ' + conflict)

                img_url = info.get('image_url', '')
                if img_url:
                    if img_url in self.image_cache:
                        self.hover_card.set_content(t, d, self.image_cache[img_url],
                                                    no_desc_text=self.str['hover_no_description'])
                    else:
                        self.hover_card.set_content(t, d, None,
                                                    no_desc_text=self.str['hover_no_description'])
                        self._fetch_image(img_url, lambda pm: self.hover_card.set_content(
                            t, d, pm, no_desc_text=self.str['hover_no_description']))
                else:
                    self.hover_card.set_content(t, d, None,
                                                no_desc_text=self.str['hover_no_description'])

            self.fetch_workshop_details(wid, on_details)
        else:
            desc = conflict if conflict else self.str['hover_no_description']
            self.hover_card.set_content(title, desc, None)
            self.hover_card.show_at(cursor_pos)

    def fetch_workshop_details(self, workshop_id, callback):
        if workshop_id in self.workshop_cache:
            callback(self.workshop_cache[workshop_id]); return
        url = QUrl("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/")
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
        data = f"itemcount=1&publishedfileids[0]={workshop_id}".encode('utf-8')
        reply = self.network_manager.post(request, data)

        def on_reply():
            info = None
            try:
                if reply.error() == QNetworkReply.NoError:
                    resp = json.loads(reply.readAll().data().decode('utf-8'))
                    details = resp.get('response', {}).get('publishedfiledetails', [])
                    if details:
                        d = details[0]
                        info = {'title': d.get('title', ''),
                                'description': d.get('description', ''),
                                'image_url': d.get('preview_url', '')}
                        self.workshop_cache[workshop_id] = info
            except Exception:
                info = None
            finally:
                reply.deleteLater()
            try: callback(info)
            except: pass

        reply.finished.connect(on_reply)

    def _fetch_image(self, image_url, callback):
        if image_url in self.image_cache:
            callback(self.image_cache[image_url]); return
        request = QNetworkRequest(QUrl(image_url))
        reply = self.network_manager.get(request)

        def on_reply():
            pm = QPixmap()
            try:
                if reply.error() == QNetworkReply.NoError:
                    pm.loadFromData(reply.readAll())
                    if not pm.isNull(): self.image_cache[image_url] = pm
            except Exception:
                pm = QPixmap()
            finally:
                reply.deleteLater()
            try: callback(pm if not pm.isNull() else None)
            except: pass

        reply.finished.connect(on_reply)

    def check_for_updates(self):
        current_version = self.current_version
        if current_version == "dev": return
        url = QUrl("https://api.github.com/repos/p4vl0-dev/kenshi-simple-mod-manager/releases/latest")
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.UserAgentHeader, "KenshiSimpleModManager/1.0")
        reply = self.network_manager.get(request)

        def handle_reply():
            try:
                if reply.error() == QNetworkReply.NoError:
                    release = json.loads(reply.readAll().data().decode('utf-8'))
                    latest_tag = release.get('tag_name', '')
                    if latest_tag.startswith('v'): latest_tag = latest_tag[1:]
                    if latest_tag and compare_versions(latest_tag, current_version) > 0:
                        self.show_update_dialog(latest_tag)
            except Exception: pass
            finally: reply.deleteLater()

        reply.finished.connect(handle_reply)

    def show_update_dialog(self, latest_version):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.str['update_available_title'])
        msg.setText(self.str['update_available_text'].format(version=latest_version))
        btn_yes = msg.addButton(self.str['yes'], QMessageBox.YesRole)
        msg.addButton(self.str['no'], QMessageBox.NoRole)
        msg.setDefaultButton(btn_yes); msg.exec_()
        if msg.clickedButton() == btn_yes:
            webbrowser.open("https://github.com/p4vl0-dev/kenshi-simple-mod-manager/releases")

# ========== ТОЧКА ВХОДА ==========
def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 22, 14))
    palette.setColor(QPalette.WindowText, QColor(232, 213, 181))
    palette.setColor(QPalette.Base, QColor(20, 16, 10))
    palette.setColor(QPalette.AlternateBase, QColor(42, 31, 21))
    palette.setColor(QPalette.ToolTipBase, QColor(42, 31, 21))
    palette.setColor(QPalette.ToolTipText, QColor(232, 213, 181))
    palette.setColor(QPalette.Text, QColor(232, 213, 181))
    palette.setColor(QPalette.Button, QColor(58, 45, 34))
    palette.setColor(QPalette.ButtonText, QColor(232, 213, 181))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, QColor(90, 69, 52))
    palette.setColor(QPalette.HighlightedText, QColor(232, 213, 181))
    app.setPalette(palette)

    icon_path = None
    base = os.path.dirname(sys.argv[0])
    if getattr(sys, 'frozen', False): base = sys._MEIPASS
    for ico in ["ksmm.ico", "ksmm.png"]:
        path = os.path.join(base, "icons", ico)
        if os.path.exists(path): icon_path = path; break
    if icon_path: app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet("""
        QMessageBox, QFileDialog, QInputDialog, QFontDialog, QColorDialog { background: #1e160e; color: #e8d5b5; }
        QMessageBox QPushButton, QFileDialog QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5a4534, stop:1 #3c2f22);
            border: 1px solid #6b5a4a; border-radius: 4px; padding: 6px 14px;
            color: #e8d5b5; font-weight: bold;
        }
        QMessageBox QPushButton:hover, QFileDialog QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6b5a4a, stop:1 #4a3a2a);
        }
        QMessageBox QPushButton:pressed, QFileDialog QPushButton:pressed { background: #2a1f15; }
        QMessageBox QLabel { color: #e8d5b5; }
        QFileDialog QListView, QFileDialog QTreeView { background: #2a1f15; color: #e8d5b5; border: 1px solid #4a3a2a; }
        QFileDialog QLineEdit { background: #2a1f15; color: #e8d5b5; border: 1px solid #4a3a2a; padding: 4px; }
        QFileDialog QComboBox { background: #2a1f15; color: #e8d5b5; border: 1px solid #4a3a2a; }
        QFileDialog QToolButton { background: transparent; color: #e8d5b5; }
        QSpinBox, QComboBox, QCheckBox, QGroupBox, QLabel { color: #e8d5b5; }
        QSpinBox, QComboBox { background: #2a1f15; border: 1px solid #4a3a2a; padding: 3px 6px; border-radius: 4px; }
        QGroupBox { border: 1px solid #4a3a2a; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
    """)

    window = ModManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()