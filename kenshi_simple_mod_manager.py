import sys
import os
import json
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
                             QLabel, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QPoint, pyqtSignal, QUrl, QSettings
from PyQt5.QtGui import (QIcon, QPixmap, QPainter, QPen, QColor, QFontDatabase,
                         QFont, QBrush, QPalette, QCursor)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import ctypes
import ctypes.wintypes

# ========== Функции для работы с версиями ==========
def get_file_version(file_path):
    """Возвращает строку версии файла (major.minor.patch) или None."""
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(file_path, None)
        if size == 0:
            return None
        buffer = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(file_path, 0, size, buffer)

        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [
                ("dwSignature", ctypes.c_uint),
                ("dwStrucVersion", ctypes.c_uint),
                ("dwFileVersionMS", ctypes.c_uint),
                ("dwFileVersionLS", ctypes.c_uint),
                ("dwProductVersionMS", ctypes.c_uint),
                ("dwProductVersionLS", ctypes.c_uint),
                ("dwFileFlagsMask", ctypes.c_uint),
                ("dwFileFlags", ctypes.c_uint),
                ("dwFileOS", ctypes.c_uint),
                ("dwFileType", ctypes.c_uint),
                ("dwFileSubtype", ctypes.c_uint),
                ("dwFileDateMS", ctypes.c_uint),
                ("dwFileDateLS", ctypes.c_uint),
            ]

        ptr = ctypes.c_void_p()
        ctypes.windll.version.VerQueryValueW(buffer, "\\", ctypes.byref(ptr), ctypes.byref(ctypes.c_uint()))
        info = ctypes.cast(ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents

        major = (info.dwFileVersionMS >> 16) & 0xFFFF
        minor = info.dwFileVersionMS & 0xFFFF
        patch = (info.dwFileVersionLS >> 16) & 0xFFFF
        # build = info.dwFileVersionLS & 0xFFFF
        return f"{major}.{minor}.{patch}"
    except Exception:
        return None

def parse_version(v):
    """Преобразует строку версии в кортеж целых чисел."""
    parts = v.split('.')
    return tuple(int(p) for p in parts[:3])

def compare_versions(v1, v2):
    """
    Сравнивает две версии.
    Возвращает:
        1, если v1 > v2
        -1, если v1 < v2
        0, если равны
    """
    t1 = parse_version(v1)
    t2 = parse_version(v2)
    for a, b in zip(t1, t2):
        if a > b:
            return 1
        elif a < b:
            return -1
    if len(t1) > len(t2):
        return 1
    elif len(t1) < len(t2):
        return -1
    return 0

# ========== Словари локализации ==========
LANGUAGES = {
    'ru': {
        'window_title': 'Менеджер модов Kenshi',
        'menu_file': 'Файл',
        'menu_load_cfg': 'Загрузить CFG',
        'menu_backup': 'Сделать бэкап mods.cfg',
        'menu_exit': 'Выход',
        'menu_view': 'Вид',
        'menu_refresh': 'Обновить список',
        'menu_manual_paths': 'Указать путь к Kenshi',
        'menu_diagnostic': 'Диагностика',
        'menu_help': 'Справка',
        'menu_about': 'О программе',
        'about_text': (
            'Упрощённый менеджер модов для Kenshi.\n\n'
            'Возможности:\n'
            '• Включать/выключать моды (ПКМ по моду)\n'
            '• Изменять порядок загрузки перетаскиванием (drag‑and‑drop)\n'
            '• Автоматическое сканирование локальных модов и модов из Steam Workshop\n'
            '• Отображение названий из файлов .info\n'
            '• Проверка зависимостей и подсветка конфликтов\n'
            '• Сохранение порядка в mods.cfg с созданием бэкапа\n'
            '• Загрузка временного списка из любого .cfg файла\n'
            '• Быстрый поиск по названиям\n'
            '• Открытие страниц модов в Steam Workshop\n'
            '• Запуск игры (через Steam или напрямую)'
        ),
        'btn_save': 'Сохранить порядок',
        'btn_launch': 'Запустить игру',
        'btn_lang': 'ENG',
        'github_url': 'https://github.com/p4vl0-dev/kenshi-simple-mod-manager',
        'search_placeholder': 'Поиск мода...',
        'header_enabled': 'Включенные моды',
        'header_disabled': 'Выключенные моды',
        'status_ready': 'Готов',
        'status_init': 'Инициализация...',
        'status_found_kenshi': 'Найдена Kenshi: {}',
        'status_not_found_kenshi': 'Kenshi не найдена автоматически.',
        'status_paths_not_set': 'Пути не найдены. Используйте меню Вид → Указать путь к Kenshi.',
        'status_manual_cancel': 'Ручной ввод отменён.',
        'status_workshop_scan': 'Workshop: {} папок, из них с .mod: {}',
        'status_backup_created': 'Бэкап создан: {}',
        'status_backup_failed': 'Не удалось создать бэкап: {}',
        'status_loaded_mods': 'Загружено {} модов (включено: {}, выключено: {})',
        'status_saved_mods': 'Сохранено {} модов в {}',
        'status_game_launched': 'Игра запущена.',
        'status_game_running': 'Игра запущена и работает.',
        'status_mod_toggled': 'Мод "{}" {} (всего включено: {})',
        'mod_status_enabled': 'включён',
        'mod_status_disabled': 'выключен',
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
        'warning_mod_not_found': 'Мод "{}" не найден в текущем списке.',
        'question_confirm_refresh': 'Обновить список модов?',
        'question_workshop_manual': 'Автоматически не удалось найти workshop.\nУказать вручную?',
        'question_duplicates_save': 'Обнаружены дублирующиеся моды.\nВы уверены, что хотите сохранить список?\n(Будут записаны только выбранные моды)',
        'info_save_success': 'mods.cfg успешно обновлён!',
        'info_mod_not_workshop': 'Мод "{}" не найден в мастерской Steam.',
        'confirm_title': 'Подтверждение',
        'error_title': 'Ошибка',
        'warning_title': 'Предупреждение',
        'info_title': 'Информация',
        'duplicate_dialog_title': 'Дублирующиеся моды',
        'duplicate_dialog_label': 'Обнаружены следующие дубликаты:',
        'duplicate_workshop_link': 'Страница в Workshop',
        'duplicate_local_label': 'Локальный',
        'save_dialog_text': 'Вы внесли изменения в список модов. Что сделать?',
        'save_btn_save': 'Сохранить',
        'save_btn_backup': 'Сохранить с бэкапом',
        'save_btn_cancel': 'Отмена',
        'backup_choose_title': 'Куда сохранить бэкап mods.cfg?',
        'backup_filter': 'CFG Files (*.cfg);;All Files (*)',
        'yes': 'Да',
        'no': 'Нет',
        'update_available_title': 'Доступно обновление',
        'update_available_text': 'Доступна новая версия {version}.\n\nВы хотите перейти на страницу загрузки?',
    },
    'en': {
        'window_title': 'Kenshi Simple Mod Manager',
        'menu_file': 'File',
        'menu_load_cfg': 'Load CFG',
        'menu_backup': 'Backup mods.cfg',
        'menu_exit': 'Exit',
        'menu_view': 'View',
        'menu_refresh': 'Refresh list',
        'menu_manual_paths': 'Set Kenshi path',
        'menu_diagnostic': 'Diagnostic',
        'menu_help': 'Help',
        'menu_about': 'About',
        'about_text': (
            'Simplified mod manager for Kenshi.\n\n'
            'Features:\n'
            '• Enable/disable mods (right‑click on mod)\n'
            '• Change load order by drag‑and‑drop\n'
            '• Automatic scanning of local and Steam Workshop mods\n'
            '• Display titles from .info files\n'
            '• Dependency checking and conflict highlighting\n'
            '• Save order to mods.cfg with backup option\n'
            '• Load temporary list from any .cfg file\n'
            '• Quick search by names\n'
            '• Open mod pages in Steam Workshop\n'
            '• Launch game (via Steam or directly)'
        ),
        'btn_save': 'Save order',
        'btn_launch': 'Launch game',
        'btn_lang': 'РУС',
        'github_url': 'https://github.com/p4vl0-dev/kenshi-simple-mod-manager',
        'search_placeholder': 'Search mod...',
        'header_enabled': 'Enabled mods',
        'header_disabled': 'Disabled mods',
        'status_ready': 'Ready',
        'status_init': 'Initializing...',
        'status_found_kenshi': 'Kenshi found: {}',
        'status_not_found_kenshi': 'Kenshi not found automatically.',
        'status_paths_not_set': 'Paths not set. Use View → Set Kenshi path.',
        'status_manual_cancel': 'Manual input cancelled.',
        'status_workshop_scan': 'Workshop: {} folders, with .mod: {}',
        'status_backup_created': 'Backup created: {}',
        'status_backup_failed': 'Failed to create backup: {}',
        'status_loaded_mods': 'Loaded {} mods (enabled: {}, disabled: {})',
        'status_saved_mods': 'Saved {} mods to {}',
        'status_game_launched': 'Game launched.',
        'status_game_running': 'Game is running.',
        'status_mod_toggled': 'Mod "{}" {} (total enabled: {})',
        'mod_status_enabled': 'enabled',
        'mod_status_disabled': 'disabled',
        'status_cfg_loaded': 'Temporary list loaded from {}. Press "Save order" to apply.',
        'status_mod_selected_workshop': 'Selected mod "{}" (has Workshop page)',
        'status_mod_selected_local': 'Selected mod "{}" (local, no Workshop page)',
        'tooltip_workshop': 'Open in Workshop',
        'tooltip_folder': 'Open mod folder',
        'tooltip_duplicate': 'Duplicates found! Click to check',
        'error_mods_folder': 'Mods folder not found.',
        'error_read_cfg': 'Failed to read mods.cfg:\n{}',
        'error_save_cfg': 'Failed to save file:\n{}',
        'error_launch_game': 'Failed to launch game:\n{}',
        'warning_no_mods': 'No mods found (with .mod file).',
        'warning_missing_mods': 'Following mods from mods.cfg not found:\n{}',
        'warning_mod_not_found': 'Mod "{}" not found in current list.',
        'question_confirm_refresh': 'Refresh mod list?',
        'question_workshop_manual': 'Workshop could not be found automatically.\nSpecify manually?',
        'question_duplicates_save': 'Duplicate mods detected.\nAre you sure you want to save the list?\n(Only selected mods will be written)',
        'info_save_success': 'mods.cfg successfully updated!',
        'info_mod_not_workshop': 'Mod "{}" not found in Steam Workshop.',
        'confirm_title': 'Confirm',
        'error_title': 'Error',
        'warning_title': 'Warning',
        'info_title': 'Information',
        'duplicate_dialog_title': 'Duplicate mods',
        'duplicate_dialog_label': 'Following duplicates found:',
        'duplicate_workshop_link': 'Workshop page',
        'duplicate_local_label': 'Local',
        'save_dialog_text': 'You have made changes to the mod list. What to do?',
        'save_btn_save': 'Save',
        'save_btn_backup': 'Save with backup',
        'save_btn_cancel': 'Cancel',
        'backup_choose_title': 'Where to save the backup of mods.cfg?',
        'backup_filter': 'CFG Files (*.cfg);;All Files (*)',
        'yes': 'Yes',
        'no': 'No',
        'update_available_title': 'Update available',
        'update_available_text': 'A new version {version} is available.\n\nDo you want to go to the download page?',
    }
}

# ========== Иконки ==========
class IconFactory:
    @staticmethod
    def create_check_icon():
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(0, 200, 0))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 16, 16, 3, 3)
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(4, 8, 7, 11)
        painter.drawLine(7, 11, 12, 4)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_cross_icon():
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(200, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 16, 16, 3, 3)
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(3, 3, 13, 13)
        painter.drawLine(13, 3, 3, 13)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_steam_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        local_ico = os.path.join(base, "icons", "steam_tray.ico")
        if os.path.exists(local_ico):
            return QIcon(local_ico)

        steam_path = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
        except:
            pass

        if steam_path:
            ico_path = os.path.join(steam_path, "public", "steam_tray.ico")
            if os.path.exists(ico_path):
                return QIcon(ico_path)

        drives = [chr(d) + ":" for d in range(ord('C'), ord('Z')+1)]
        for drive in drives:
            ico_path = os.path.join(drive, "Program Files (x86)", "Steam", "public", "steam_tray.ico")
            if os.path.exists(ico_path):
                return QIcon(ico_path)
            ico_path = os.path.join(drive, "Program Files", "Steam", "public", "steam_tray.ico")
            if os.path.exists(ico_path):
                return QIcon(ico_path)

        return IconFactory._create_fallback_steam_icon()

    @staticmethod
    def _create_fallback_steam_icon():
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(100, 150, 255))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 16, 16, 3, 3)
        painter.setPen(QPen(Qt.white, 1))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "S")
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_folder_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        folder_path = os.path.join(base, "icons", "folder.webp")
        if os.path.exists(folder_path):
            return QIcon(folder_path)
        else:
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QColor(200, 180, 150))
            painter.setPen(QPen(QColor(140, 120, 100), 1))
            painter.drawRoundedRect(2, 4, 12, 10, 2, 2)
            painter.drawLine(4, 4, 6, 2)
            painter.drawLine(6, 2, 10, 2)
            painter.drawLine(10, 2, 12, 4)
            painter.end()
            return QIcon(pixmap)

    @staticmethod
    def create_duplicate_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        warning_path = os.path.join(base, "icons", "warning.webp")
        if os.path.exists(warning_path):
            return QIcon(warning_path)
        else:
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(255, 200, 0))
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            points = [QPoint(8, 2), QPoint(14, 14), QPoint(2, 14)]
            painter.drawPolygon(*points)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(8, 6, 8, 10)
            painter.drawLine(8, 12, 8, 13)
            painter.end()
            return QIcon(pixmap)

    @staticmethod
    def create_github_icon():
        base = os.path.dirname(sys.argv[0])
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        github_path = os.path.join(base, "icons", "github.webp")
        if os.path.exists(github_path):
            return QIcon(github_path)
        else:
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 20, 20)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "G")
            painter.end()
            return QIcon(pixmap)

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
        if not (index.flags() & Qt.ItemIsSelectable):
            return

        rect = option.rect
        mod_name = index.data(Qt.UserRole + 3) or index.data(Qt.DisplayRole)
        parent = self.parent()
        has_duplicate = False
        if parent and hasattr(parent, 'mod_dubles'):
            has_duplicate = mod_name in parent.mod_dubles

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
            if self.animating and self.hovered_index == index:
                size = self.icon_size + 4
            offset = (size - self.icon_size) // 2
            icon_rect = QRect(rect.right() - size - 5 - offset,
                              rect.top() + (rect.height() - size) // 2,
                              size, size)
            self.steam_icon.paint(painter, icon_rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)
        else:
            self.folder_icon.paint(painter, icon_rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)

        if index.data(Qt.UserRole + 1):
            painter.save()
            pen = QPen(QColor(255, 255, 0), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()

    def helpEvent(self, event, view, option, index):
        if not (index.flags() & Qt.ItemIsSelectable):
            return False

        rect = option.rect
        mod_name = index.data(Qt.UserRole + 3) or index.data(Qt.DisplayRole)
        parent = self.parent()
        has_duplicate = False
        if parent and hasattr(parent, 'mod_dubles'):
            has_duplicate = mod_name in parent.mod_dubles

        dup_rect = None
        if has_duplicate:
            dup_rect = QRect(rect.right() - self.dup_icon_size - 5 - self.icon_size - 5,
                             rect.top() + (rect.height() - self.dup_icon_size) // 2,
                             self.dup_icon_size, self.dup_icon_size)
        icon_rect = QRect(rect.right() - self.icon_size - 5,
                          rect.top() + (rect.height() - self.icon_size) // 2,
                          self.icon_size, self.icon_size)
        text_rect = rect
        if dup_rect:
            text_rect.setRight(dup_rect.left() - 5)
        if icon_rect:
            text_rect.setRight(text_rect.right() - self.icon_size - 5)

        pos = event.pos()
        if dup_rect and dup_rect.contains(pos):
            QToolTip.showText(event.globalPos(), self.tooltip_duplicate)
            return True
        elif icon_rect.contains(pos):
            workshop_id = index.data(Qt.UserRole)
            if workshop_id:
                QToolTip.showText(event.globalPos(), self.tooltip_workshop)
            else:
                QToolTip.showText(event.globalPos(), self.tooltip_folder)
            return True
        elif text_rect.contains(pos):
            title = index.data(Qt.UserRole + 4)
            conflict_text = index.data(Qt.UserRole + 5)
            tooltip_parts = []
            if title:
                tooltip_parts.append(title)
            if conflict_text:
                tooltip_parts.append(f"⚠ {conflict_text}")
            if tooltip_parts:
                QToolTip.showText(event.globalPos(), "\n".join(tooltip_parts))
            else:
                QToolTip.hideText()
            return True
        else:
            QToolTip.hideText()
            return True

    def editorEvent(self, event, model, option, index):
        if not (index.flags() & Qt.ItemIsSelectable):
            return False

        rect = option.rect
        mod_name = index.data(Qt.UserRole + 3) or index.data(Qt.DisplayRole)
        parent = self.parent()
        has_duplicate = False
        if parent and hasattr(parent, 'mod_dubles'):
            has_duplicate = mod_name in parent.mod_dubles

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
                    parent.show_duplicate_dialog(mod_name)
                return True
            if icon_rect.contains(event.pos()):
                workshop_id = index.data(Qt.UserRole)
                view = option.widget
                if workshop_id:
                    self.animating = True
                    self.hovered_index = index
                    if view:
                        view.viewport().update()
                    def open_url():
                        webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}")
                        self.animating = False
                        self.hovered_index = None
                        if view:
                            view.viewport().update()
                    QTimer.singleShot(150, open_url)
                    return True
                else:
                    self.animating = True
                    self.hovered_index = index
                    if view:
                        view.viewport().update()
                    def open_folder():
                        mod_path = parent.mod_paths.get(mod_name) if parent else None
                        if mod_path and os.path.exists(mod_path):
                            if sys.platform == 'win32':
                                os.startfile(mod_path)
                            else:
                                subprocess.Popen(['xdg-open', mod_path])
                        self.animating = False
                        self.hovered_index = None
                        if view:
                            view.viewport().update()
                    QTimer.singleShot(150, open_folder)
                    return True
        return False

# ========== Диалог дубликатов ==========
class DuplicateDialog(QDialog):
    def __init__(self, mod_name, duplicates, parent=None):
        super().__init__(parent)
        self.setWindowTitle(parent.str['duplicate_dialog_title'] if parent else "Duplicate mods")
        self.setMinimumSize(500, 300)
        self.duplicates = duplicates
        self.parent_ref = parent

        layout = QVBoxLayout(self)
        label = QLabel(parent.str['duplicate_dialog_label'] if parent else "Found duplicates:")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        for dup in duplicates:
            info = dup.get('info')
            title = info.get('title') if info else None
            file_name = mod_name
            if title and title != file_name:
                display_text = f"{title} ({file_name})"
            else:
                display_text = file_name

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, dup)
            if dup.get('workshop_id'):
                item.setIcon(IconFactory.create_steam_icon())
            else:
                item.setIcon(IconFactory.create_folder_icon())
            self.list_widget.addItem(item)

        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setStyleSheet(parent.styleSheet() if parent else "")

    def on_item_clicked(self, item):
        dup = item.data(Qt.UserRole)
        if dup:
            workshop_id = dup.get('workshop_id')
            if workshop_id:
                url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
                webbrowser.open(url)
            else:
                mod_path = dup.get('path')
                if mod_path and os.path.exists(mod_path):
                    if sys.platform == 'win32':
                        os.startfile(mod_path)
                    else:
                        subprocess.Popen(['xdg-open', mod_path])

# ========== Список с сигналом, плавным автоскроллом и запретом перетаскивания между секциями ==========
class ModListWidget(QListWidget):
    listChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMouseTracking(True)

        self.scroll_zone_size = 40
        self.scroll_base_speed = 8
        self.autoscroll_timer = QTimer(self)
        self.autoscroll_timer.setInterval(16)
        self.autoscroll_timer.timeout.connect(self.do_autoscroll)
        self._drag_active = False

    def _check_same_section(self, source_row, target_row):
        source_section = self.get_section(source_row)
        target_section = self.get_section(target_row)
        return source_section == target_section and source_section != -1

    def dragMoveEvent(self, event):
        source_item = self.currentItem()
        if source_item:
            source_row = self.row(source_item)
            target_item = self.itemAt(event.pos())
            if target_item:
                target_row = self.row(target_item)
                if not self._check_same_section(source_row, target_row):
                    event.ignore()
                    return

        self._drag_active = True
        if self._is_in_scroll_zone(event.pos()):
            if not self.autoscroll_timer.isActive():
                self.autoscroll_timer.start()
        else:
            self.autoscroll_timer.stop()
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        source_item = self.currentItem()
        if source_item:
            source_row = self.row(source_item)
            target_item = self.itemAt(event.pos())
            if target_item:
                target_row = self.row(target_item)
                if not self._check_same_section(source_row, target_row):
                    event.ignore()
                    return

        self.autoscroll_timer.stop()
        self._drag_active = False
        super().dropEvent(event)
        self.listChanged.emit()

    def do_autoscroll(self):
        if not self._drag_active:
            self.autoscroll_timer.stop()
            return
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        if not self.viewport().rect().contains(pos):
            self.autoscroll_timer.stop()
            return
        if not self._is_in_scroll_zone(pos):
            self.autoscroll_timer.stop()
            return

        v_scrollbar = self.verticalScrollBar()
        height = self.viewport().height()
        if pos.y() < self.scroll_zone_size:
            normalized = 1.0 - (pos.y() / self.scroll_zone_size)
            direction = -1
        else:
            normalized = (pos.y() - (height - self.scroll_zone_size)) / self.scroll_zone_size
            direction = 1
        delta = int(self.scroll_base_speed * (0.2 + 0.8 * normalized))
        v_scrollbar.setValue(v_scrollbar.value() + direction * delta)

    def _is_in_scroll_zone(self, pos):
        height = self.viewport().height()
        return (pos.y() < self.scroll_zone_size) or (pos.y() > (height - self.scroll_zone_size))

    def get_section(self, row):
        if row < 0:
            return -1
        item = self.item(row)
        if not (item.flags() & Qt.ItemIsSelectable):
            return -1
        for i in range(row - 1, -1, -1):
            if not (self.item(i).flags() & Qt.ItemIsSelectable):
                text = self.item(i).text()
                if text in ("Включенные моды", "Enabled mods"):
                    return 0
                elif text in ("Выключенные моды", "Disabled mods"):
                    return 1
        return 0

# ========== Вспомогательные функции ==========
def get_mod_dependencies(mod_folder):
    return []

def read_mod_info(folder_path):
    for f in os.listdir(folder_path):
        if f.lower() in ('info', 'info.xml', 'modinfo.xml') or f.lower().endswith('.info'):
            info_file = os.path.join(folder_path, f)
            try:
                tree = ET.parse(info_file)
                root = tree.getroot()
                title = root.find('title')
                mod_id = root.find('id')
                return {'title': title.text if title is not None else None,
                        'id': mod_id.text if mod_id is not None else None}
            except:
                continue
    return None

# ========== ГЛАВНОЕ ОКНО ==========
class ModManager(QMainWindow):
    def __init__(self):
        super().__init__()
        # Инициализация QSettings для сохранения языка
        self.settings = QSettings("p4vl0-dev", "KenshiSimpleModManager")
        saved_lang = self.settings.value("language", "ru")
        self.current_lang = saved_lang if saved_lang in LANGUAGES else "ru"
        self.str = LANGUAGES[self.current_lang]
        self.current_version = get_file_version(sys.argv[0]) or "dev"
        self.setWindowTitle(f"{self.str['window_title']} v{self.current_version}")
        self.setMinimumSize(750, 700)

        icon_path = self.find_resource("ksmm.ico")
        if not icon_path:
            icon_path = self.find_resource("ksmm.png")
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        font_path = self.find_resource("Kenshi.ttf", subdir="fonts")
        if font_path and os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                self.setFont(QFont(font_family, 10))

        self.exo_font = None
        exo_path = self.find_resource("Exo2-Bold.ttf", subdir="fonts")
        if exo_path and os.path.exists(exo_path):
            font_id = QFontDatabase.addApplicationFont(exo_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                self.exo_font = QFont(font_family, 12, QFont.Bold)

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
        self.search_current_index = -1

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Меню
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: #2a1f15;
                color: #e8d5b5;
                font-weight: bold;
                spacing: 0px;
            }
            QMenuBar::item {
                padding: 6px 10px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #5a4534;
            }
            QMenu {
                background: #2a1f15;
                color: #e8d5b5;
                border: 1px solid #4a3a2a;
            }
            QMenu::item:selected {
                background: #5a4534;
            }
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
        self.action_manual_paths = QAction(self.str['menu_manual_paths'], self)
        self.action_manual_paths.triggered.connect(self.manual_paths)
        self.view_menu.addAction(self.action_manual_paths)
        self.action_diagnostic = QAction(self.str['menu_diagnostic'], self)
        self.action_diagnostic.triggered.connect(self.show_diagnostic)
        self.view_menu.addAction(self.action_diagnostic)

        self.help_menu = menubar.addMenu(self.str['menu_help'])
        self.action_about = QAction(self.str['menu_about'], self)
        self.action_about.triggered.connect(self.show_about)
        self.help_menu.addAction(self.action_about)

        # GitHub и языковая кнопка
        self.btn_github = QPushButton()
        self.btn_github.setIcon(IconFactory.create_github_icon())
        self.btn_github.setIconSize(QSize(20, 20))
        self.btn_github.setFlat(True)
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.clicked.connect(lambda: webbrowser.open(self.str['github_url']))
        self.btn_github.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px 6px;
            }
            QPushButton:hover {
                background: #5a4534;
                border-radius: 4px;
            }
        """)
        self.btn_github.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.btn_lang = QPushButton(self.str['btn_lang'])
        self.btn_lang.setObjectName("btn_lang")
        self.btn_lang.clicked.connect(self.toggle_language)
        self.btn_lang.setStyleSheet("""
            QPushButton#btn_lang {
                background: transparent;
                border: none;
                padding: 6px 10px;
                color: #e8d5b5;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#btn_lang:hover {
                background: #5a4534;
            }
        """)
        self.btn_lang.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(2)
        corner_layout.addWidget(self.btn_github)
        corner_layout.addWidget(self.btn_lang)
        self.menuBar().setCornerWidget(corner_widget, Qt.TopRightCorner)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.str['search_placeholder'])
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #2a1f15;
                color: #e8d5b5;
                border: 1px solid #4a3a2a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        search_layout.addWidget(self.search_input)

        self.btn_search_up = QPushButton("▲")
        self.btn_search_up.setFixedSize(24, 24)
        self.btn_search_up.clicked.connect(self.search_prev)
        self.btn_search_up.setStyleSheet(self.button_style())
        search_layout.addWidget(self.btn_search_up)

        self.btn_search_down = QPushButton("▼")
        self.btn_search_down.setFixedSize(24, 24)
        self.btn_search_down.clicked.connect(self.search_next)
        self.btn_search_down.setStyleSheet(self.button_style())
        search_layout.addWidget(self.btn_search_down)

        main_layout.insertLayout(1, search_layout)

        # Список
        self.list_widget = ModListWidget(self)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.delegate = ModItemDelegate(self)
        self.list_widget.setItemDelegate(self.delegate)
        self.list_widget.listChanged.connect(self.on_list_changed)
        self.list_widget.currentItemChanged.connect(self.on_current_mod_changed)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #1e160e;
                border: 1px solid #4a3a2a;
                border-radius: 6px;
                outline: none;
                font-weight: bold;
                font-size: 13px;
                color: #e8d5b5;
            }
            QListWidget::item {
                border-bottom: 1px solid #3a2c1e;
                padding: 6px 10px;
                background: #2a1f15;
            }
            QListWidget::item:selected {
                background: #5a4534;
            }
            QScrollBar:vertical {
                background: #1e160e;
                width: 18px;
                border-radius: 9px;
            }
            QScrollBar::handle:vertical {
                background: #5a4534;
                border-radius: 9px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        main_layout.addWidget(self.list_widget)

        # Кнопки внизу
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_save = QPushButton(self.str['btn_save'])
        self.btn_save.clicked.connect(self.save_mods)
        self.btn_save.setEnabled(False)
        self.btn_save.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        btn_layout.addWidget(self.btn_save)

        self.btn_launch = QPushButton(self.str['btn_launch'])
        self.btn_launch.clicked.connect(self.launch_game)
        self.btn_launch.setStyleSheet(self.button_style())
        self.btn_launch.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        btn_layout.addWidget(self.btn_launch)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #1e160e;
                color: #b09a80;
                border-top: 1px solid #3a2c1e;
                padding: 4px;
                font-weight: bold;
            }
        """)
        self.statusBar().showMessage(self.str['status_init'])

        self.setStyleSheet("""
            QMainWindow {
                background: #1e160e;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #5a4534, stop:1 #3c2f22);
                border: 1px solid #6b5a4a;
                border-radius: 4px;
                padding: 6px 14px;
                color: #e8d5b5;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #6b5a4a, stop:1 #4a3a2a);
            }
            QPushButton:pressed {
                background: #2a1f15;
            }
            QToolTip {
                background: #2a1f15;
                color: #e8d5b5;
                border: 1px solid #4a3a2a;
                padding: 4px;
            }
        """)

        self.auto_detect_paths()
        if self.mods_cfg_path and os.path.exists(self.mods_cfg_path):
            self.load_mods(ask_confirmation=False)
        else:
            self.statusBar().showMessage(self.str['status_paths_not_set'])

        # Запуск проверки обновлений через 1.5 секунды после инициализации
        QTimer.singleShot(1500, self.check_for_updates)

    # ========== Локализация ==========
    def toggle_language(self):
        self.current_lang = 'en' if self.current_lang == 'ru' else 'ru'
        self.settings.setValue("language", self.current_lang)
        self.str = LANGUAGES[self.current_lang]
        self.update_ui_texts()
        self.build_list(self.enabled_list, self.disabled_list)

    def update_ui_texts(self):
        self.setWindowTitle(f"{self.str['window_title']} v{self.current_version}")
        self.file_menu.setTitle(self.str['menu_file'])
        self.action_load_cfg.setText(self.str['menu_load_cfg'])
        self.action_backup.setText(self.str['menu_backup'])
        self.action_exit.setText(self.str['menu_exit'])
        self.view_menu.setTitle(self.str['menu_view'])
        self.action_refresh.setText(self.str['menu_refresh'])
        self.action_manual_paths.setText(self.str['menu_manual_paths'])
        self.action_diagnostic.setText(self.str['menu_diagnostic'])
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

    # ========== Поиск ==========
    def on_search(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                item.setData(Qt.UserRole + 1, False)
                mod_name = item.data(Qt.UserRole + 3) or item.text()
                conflicts = self.check_dependencies([m for m, s in self.mod_status.items() if s])
                if mod_name in conflicts:
                    item.setBackground(QBrush(QColor(180, 150, 50)))
                else:
                    item.setBackground(QBrush(Qt.transparent))
        if text:
            text_lower = text.lower()
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.flags() & Qt.ItemIsSelectable:
                    display_text = item.text().lower()
                    title = item.data(Qt.UserRole + 4) or ""
                    if text_lower in display_text or text_lower in title.lower():
                        item.setData(Qt.UserRole + 1, True)
                        mod_name = item.data(Qt.UserRole + 3) or item.text()
                        conflicts = self.check_dependencies([m for m, s in self.mod_status.items() if s])
                        if mod_name in conflicts:
                            item.setBackground(QBrush(QColor(180, 150, 50)))
                        else:
                            item.setBackground(QBrush(Qt.transparent))
        self.list_widget.viewport().update()

    def search_next(self):
        if not self.search_input.text():
            return
        text = self.search_input.text().lower()
        start = self.list_widget.currentRow() + 1 if self.list_widget.currentRow() >= 0 else 0
        for i in range(start, self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i)
                return
        for i in range(0, self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i)
                return

    def search_prev(self):
        if not self.search_input.text():
            return
        text = self.search_input.text().lower()
        start = self.list_widget.currentRow() - 1 if self.list_widget.currentRow() >= 0 else self.list_widget.count() - 1
        for i in range(start, -1, -1):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i)
                return
        for i in range(self.list_widget.count() - 1, -1, -1):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable and text in item.text().lower():
                self.list_widget.setCurrentRow(i)
                return

    # ========== Диалог дубликата ==========
    def show_duplicate_dialog(self, mod_name):
        duplicates = self.mod_dubles.get(mod_name, [])
        if not duplicates:
            return
        dlg = DuplicateDialog(mod_name, duplicates, self)
        dlg.exec_()

    # ========== Диагностика ==========
    def show_diagnostic(self):
        workshop_count = len([m for m in self.workshop_ids if self.workshop_ids[m] is not None])
        local_count = len([m for m in self.mod_paths.keys() if m not in self.workshop_ids])
        unique_total = len(self.mod_paths)
        game_exe = self.find_game_exe()
        msg = f"=== ДИАГНОСТИКА ===\n"
        msg += f"Путь к Kenshi: {self.kenshi_path or 'НЕ НАЙДЕН'}\n"
        msg += f"Исполняемый файл игры: {game_exe or 'НЕ НАЙДЕН'}\n"
        msg += f"Файл mods.cfg: {self.mods_cfg_path or 'НЕ НАЙДЕН'}\n"
        msg += f"Всего папок в workshop: {len(os.listdir(self.workshop_folder)) if self.workshop_folder and os.path.exists(self.workshop_folder) else 0}\n"
        msg += f"Папок с .mod: {workshop_count}\n"
        msg += f"Локальных модов: {local_count}\n"
        msg += f"Уникальных модов (после объединения): {unique_total}\n"
        msg += f"Дублей (групп с >1 мода): {len(self.mod_dubles)}\n\n"
        if self.mod_dubles:
            msg += "Группы дублей:\n"
            for name, dups in self.mod_dubles.items():
                msg += f"  {name} ({len(dups)} дублей)\n"
        QMessageBox.information(self, "Диагностика", msg)

    # ========== Поиск ресурсов ==========
    def find_resource(self, filename, subdir=""):
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))

        candidates = []
        if subdir:
            candidates.append(os.path.join(base, subdir, filename))
        candidates.append(os.path.join(base, filename))

        exe_base = os.path.dirname(os.path.abspath(sys.argv[0]))
        if subdir:
            candidates.append(os.path.join(exe_base, subdir, filename))
        candidates.append(os.path.join(exe_base, filename))

        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    # ========== Поиск Kenshi ==========
    def auto_detect_paths(self):
        self.kenshi_path = self.find_kenshi_path()
        if self.kenshi_path:
            self.kenshi_path = os.path.normpath(os.path.abspath(self.kenshi_path))
            self.update_paths(self.kenshi_path)
            self.statusBar().showMessage(self.str['status_found_kenshi'].format(self.kenshi_path))
        else:
            self.statusBar().showMessage(self.str['status_not_found_kenshi'])

    def find_game_exe(self):
        if not self.kenshi_path:
            return None
        exe_candidates = [
            os.path.join(self.kenshi_path, "kenshi_x64.exe"),
            os.path.join(self.kenshi_path, "kenshi.exe"),
            os.path.join(self.kenshi_path, "Kenshi_x64.exe"),
            os.path.join(self.kenshi_path, "Kenshi.exe"),
        ]
        for candidate in exe_candidates:
            if os.path.exists(candidate):
                return candidate
        return None

    def find_kenshi_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
            candidate = os.path.join(steam_path, "steamapps", "common", "Kenshi")
            if os.path.exists(os.path.join(candidate, "data", "mods.cfg")):
                return os.path.abspath(candidate)
        except:
            pass

        drives = [chr(d) + ":" for d in range(ord('C'), ord('Z')+1)]
        for drive in drives:
            bases = [
                os.path.join(drive, "SteamLibrary", "steamapps", "common", "Kenshi"),
                os.path.join(drive, "Program Files (x86)", "Steam", "steamapps", "common", "Kenshi"),
                os.path.join(drive, "Program Files", "Steam", "steamapps", "common", "Kenshi"),
            ]
            for base in bases:
                if os.path.exists(os.path.join(base, "data", "mods.cfg")):
                    return os.path.abspath(base)

        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.exists(os.path.join(exe_dir, "data", "mods.cfg")):
            return os.path.abspath(exe_dir)

        parent_dir = os.path.dirname(exe_dir)
        if os.path.exists(os.path.join(parent_dir, "data", "mods.cfg")):
            return os.path.abspath(parent_dir)

        return None

    def update_paths(self, kenshi_path):
        self.kenshi_path = kenshi_path
        self.mods_folder = os.path.join(kenshi_path, "mods")
        self.workshop_folder = self.find_workshop_path(kenshi_path)
        self.mods_cfg_path = os.path.join(kenshi_path, "data", "mods.cfg")

    def find_workshop_path(self, kenshi_path):
        steamapps = os.path.dirname(kenshi_path)
        if os.path.basename(steamapps) != "steamapps":
            steamapps = os.path.dirname(steamapps)
        candidate = os.path.join(steamapps, "workshop", "content", "233860")
        if os.path.exists(candidate):
            return candidate

        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
            candidate = os.path.join(steam_path, "steamapps", "workshop", "content", "233860")
            if os.path.exists(candidate):
                return candidate
        except:
            pass

        drives = [chr(d) + ":" for d in range(ord('C'), ord('Z')+1)]
        for drive in drives:
            candidate = os.path.join(drive, "SteamLibrary", "steamapps", "workshop", "content", "233860")
            if os.path.exists(candidate):
                return candidate
            candidate = os.path.join(drive, "Program Files (x86)", "Steam", "steamapps", "workshop", "content", "233860")
            if os.path.exists(candidate):
                return candidate
            candidate = os.path.join(drive, "Program Files", "Steam", "steamapps", "workshop", "content", "233860")
            if os.path.exists(candidate):
                return candidate
        return None

    def manual_paths(self):
        folder = QFileDialog.getExistingDirectory(self, self.str['menu_manual_paths'])
        if folder:
            self.kenshi_path = folder
            self.update_paths(folder)
            if not self.workshop_folder or not os.path.exists(self.workshop_folder):
                if self._question_box(self.str['confirm_title'], self.str['question_workshop_manual']):
                    workshop = QFileDialog.getExistingDirectory(self, "Выберите папку workshop/content/233860")
                    if workshop:
                        self.workshop_folder = workshop
            self.load_mods(ask_confirmation=False)
        else:
            self.statusBar().showMessage(self.str['status_manual_cancel'])

    # ========== Работа с модами ==========
    def has_mod_file(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".mod"):
                    return True
        return False

    def get_mod_name_from_folder(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".mod"):
                    return os.path.splitext(file)[0]
        return None

    # ========== Загрузка ==========
    def load_mods_with_confirm(self):
        if self._question_box(self.str['confirm_title'], self.str['question_confirm_refresh']):
            self.load_mods(ask_confirmation=False)

    def load_mods(self, ask_confirmation=False):
        if ask_confirmation:
            if not self._question_box(self.str['confirm_title'], self.str['question_confirm_refresh']):
                return

        if not self.mods_folder or not os.path.exists(self.mods_folder):
            QMessageBox.warning(self, self.str['error_title'], self.str['error_mods_folder'])
            return

        enabled_names = []
        if os.path.exists(self.mods_cfg_path):
            try:
                with open(self.mods_cfg_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines:
                    name = line.strip()
                    if name.lower().endswith('.mod'):
                        name = name[:-4]
                    enabled_names.append(name)
            except Exception as e:
                QMessageBox.critical(self, self.str['error_title'], self.str['error_read_cfg'].format(e))
                return

        all_mods_raw = {}
        if os.path.exists(self.mods_folder):
            for mod_dir in os.listdir(self.mods_folder):
                full_path = os.path.join(self.mods_folder, mod_dir)
                if os.path.isdir(full_path) and self.has_mod_file(full_path):
                    name = self.get_mod_name_from_folder(full_path)
                    if name:
                        if name not in all_mods_raw:
                            all_mods_raw[name] = []
                        info = read_mod_info(full_path)
                        all_mods_raw[name].append({
                            'path': full_path,
                            'workshop_id': None,
                            'info': info,
                            'display_name': info.get('title') if info else name
                        })

        if self.workshop_folder and os.path.exists(self.workshop_folder):
            for mod_id_dir in os.listdir(self.workshop_folder):
                full_path = os.path.join(self.workshop_folder, mod_id_dir)
                if os.path.isdir(full_path) and self.has_mod_file(full_path):
                    raw_name = self.get_mod_name_from_folder(full_path)
                    if raw_name:
                        if raw_name not in all_mods_raw:
                            all_mods_raw[raw_name] = []
                        info = read_mod_info(full_path)
                        all_mods_raw[raw_name].append({
                            'path': full_path,
                            'workshop_id': mod_id_dir,
                            'info': info,
                            'display_name': info.get('title') if info else raw_name
                        })

        if not all_mods_raw:
            QMessageBox.warning(self, self.str['warning_title'], self.str['warning_no_mods'])
            self.list_widget.clear()
            self.mod_status = {}
            self.mod_paths = {}
            self.mod_info = {}
            self.mod_deps = {}
            self.workshop_ids = {}
            self.mod_dubles = {}
            return

        self.mod_paths = {}
        self.mod_info = {}
        self.mod_dubles = {}
        self.workshop_ids = {}
        self.mod_deps = {}

        for base_name, items in all_mods_raw.items():
            if len(items) > 1:
                self.mod_dubles[base_name] = items
            representative = items[0]
            self.mod_paths[base_name] = representative['path']
            self.mod_info[base_name] = representative['info']
            if representative['workshop_id']:
                self.workshop_ids[base_name] = representative['workshop_id']

        self.mod_status = {}
        missing = []
        for mod_name in self.mod_paths.keys():
            self.mod_status[mod_name] = False
        for name in enabled_names:
            if name in self.mod_status:
                self.mod_status[name] = True
            else:
                missing.append(name)

        if missing:
            QMessageBox.warning(self, self.str['warning_title'], self.str['warning_missing_mods'].format(', '.join(missing)))

        enabled_list = []
        for name in enabled_names:
            if name in self.mod_status and self.mod_status[name]:
                enabled_list.append(name)
        for mod_name, status in self.mod_status.items():
            if status and mod_name not in enabled_list:
                enabled_list.append(mod_name)

        disabled_list = sorted(
            [m for m, s in self.mod_status.items() if not s]
        )

        self.enabled_list = enabled_list
        self.disabled_list = disabled_list
        self.original_enabled_list = enabled_list[:]

        self.build_list(enabled_list, disabled_list)
        self.modified = False
        self.update_save_button()
        self.statusBar().showMessage(
            self.str['status_loaded_mods'].format(len(enabled_list) + len(disabled_list), len(enabled_list), len(disabled_list))
        )

    def build_list(self, enabled_list, disabled_list):
        self.list_widget.clear()
        conflicts = self.check_dependencies(enabled_list)

        def create_item(mod_name, is_enabled):
            display_name = mod_name
            info = self.mod_info.get(mod_name)
            title = info.get('title') if info else None
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole + 3, mod_name)
            item.setData(Qt.UserRole + 4, title if title else "")
            item.setIcon(IconFactory.create_check_icon() if is_enabled else IconFactory.create_cross_icon())
            workshop_id = self.workshop_ids.get(mod_name, "")
            item.setData(Qt.UserRole, workshop_id)
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
        header_enabled.setForeground(QColor("#f0e0c8"))
        header_enabled.setBackground(QBrush(QColor("#3a2c1e")))
        header_enabled.setTextAlignment(Qt.AlignCenter)
        header_enabled.setFont(self.exo_font if self.exo_font else QFont(self.font().family(), 12, QFont.Bold))
        self.list_widget.addItem(header_enabled)

        for mod in enabled_list:
            self.list_widget.addItem(create_item(mod, True))

        header_disabled = QListWidgetItem(self.str['header_disabled'])
        header_disabled.setFlags(header_disabled.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled)
        header_disabled.setForeground(QColor("#f0e0c8"))
        header_disabled.setBackground(QBrush(QColor("#3a2c1e")))
        header_disabled.setTextAlignment(Qt.AlignCenter)
        header_disabled.setFont(self.exo_font if self.exo_font else QFont(self.font().family(), 12, QFont.Bold))
        self.list_widget.addItem(header_disabled)

        for mod in disabled_list:
            self.list_widget.addItem(create_item(mod, False))

    # ========== Проверка зависимостей ==========
    def check_dependencies(self, enabled_list):
        errors = {}
        index_map = {mod: i for i, mod in enumerate(enabled_list)}
        for mod_name in enabled_list:
            deps = self.mod_deps.get(mod_name, [])
            for dep in deps:
                if dep not in index_map:
                    errors[mod_name] = f"Отсутствует зависимость: {dep}"
                else:
                    if index_map[dep] >= index_map[mod_name]:
                        errors[mod_name] = f"Неверный порядок: {dep} должен загружаться раньше {mod_name}"
        return errors

    def update_conflict_highlights(self):
        enabled_list = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mod_name = item.data(Qt.UserRole + 3) or item.text()
                if self.mod_status.get(mod_name, False):
                    enabled_list.append(mod_name)
        conflicts = self.check_dependencies(enabled_list)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mod_name = item.data(Qt.UserRole + 3) or item.text()
                if mod_name in conflicts:
                    item.setBackground(QBrush(QColor(180, 150, 50)))
                    item.setData(Qt.UserRole + 5, conflicts[mod_name])
                else:
                    item.setBackground(QBrush(Qt.transparent))
                    item.setData(Qt.UserRole + 5, "")

    def check_if_modified(self):
        current_enabled = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mod_name = item.data(Qt.UserRole + 3) or item.text()
                if self.mod_status.get(mod_name, False):
                    current_enabled.append(mod_name)
        if current_enabled == self.original_enabled_list:
            self.modified = False
        else:
            self.modified = True
        self.update_save_button()

    # ========== Сохранение ==========
    def show_save_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.str['confirm_title'])
        msg.setText(self.str['save_dialog_text'])
        btn_save = msg.addButton(self.str['save_btn_save'], QMessageBox.AcceptRole)
        btn_backup = msg.addButton(self.str['save_btn_backup'], QMessageBox.ActionRole)
        btn_cancel = msg.addButton(self.str['save_btn_cancel'], QMessageBox.RejectRole)
        btn_backup.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        btn_save.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        btn_cancel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        msg.setDefaultButton(btn_save)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked == btn_save:
            return 'save'
        elif clicked == btn_backup:
            return 'backup'
        else:
            return 'cancel'

    def save_mods(self):
        if not self.mods_cfg_path:
            QMessageBox.warning(self, self.str['error_title'], "Путь к mods.cfg не задан.")
            return

        if self.mod_dubles:
            if not self._question_box(self.str['confirm_title'], self.str['question_duplicates_save']):
                return

        if self.modified:
            action = self.show_save_dialog()
            if action == 'cancel':
                return
            if action == 'backup':
                if not self.backup_mods_cfg_manual(show_success=False):
                    return

        enabled_in_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                mod_name = item.data(Qt.UserRole + 3) or item.text()
                if self.mod_status.get(mod_name, False):
                    enabled_in_order.append(mod_name)

        try:
            with open(self.mods_cfg_path, 'w', encoding='utf-8') as f:
                for mod_name in enabled_in_order:
                    f.write(mod_name + '.mod\n')
            self.statusBar().showMessage(self.str['status_saved_mods'].format(len(enabled_in_order), self.mods_cfg_path))
            self.original_enabled_list = enabled_in_order[:]
            self.modified = False
            self.update_save_button()
            QMessageBox.information(self, self.str['info_title'], self.str['info_save_success'])
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'], self.str['error_save_cfg'].format(e))

    def load_cfg_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.str['menu_load_cfg'], "", "CFG Files (*.cfg);;All Files (*)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            mod_names = []
            for line in lines:
                name = line.strip()
                if name.lower().endswith('.mod'):
                    name = name[:-4]
                mod_names.append(name)

            for mod in self.mod_status.keys():
                self.mod_status[mod] = False
            for mod_name in mod_names:
                if mod_name in self.mod_status:
                    self.mod_status[mod_name] = True

            enabled_list = [m for m, s in self.mod_status.items() if s]
            disabled_list = [m for m, s in self.mod_status.items() if not s]
            enabled_ordered = [m for m in mod_names if m in self.mod_status and self.mod_status[m]]
            for m in enabled_list:
                if m not in enabled_ordered:
                    enabled_ordered.append(m)
            disabled_ordered = sorted(disabled_list)
            self.enabled_list = enabled_ordered
            self.disabled_list = disabled_ordered
            self.build_list(enabled_ordered, disabled_ordered)
            self.modified = True
            self.update_save_button()
            self.statusBar().showMessage(self.str['status_cfg_loaded'].format(file_path))
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'], f"Не удалось загрузить CFG:\n{e}")

    def backup_mods_cfg_manual(self, show_success=True):
        if not self.mods_cfg_path or not os.path.exists(self.mods_cfg_path):
            QMessageBox.warning(self, self.str['error_title'], "Файл mods.cfg не найден.")
            return False
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.str['backup_choose_title'],
            os.path.join(os.path.dirname(self.mods_cfg_path), "mods_backup.cfg"),
            self.str['backup_filter']
        )
        if not file_path:
            return False
        try:
            import shutil
            shutil.copy2(self.mods_cfg_path, file_path)
            if show_success:
                self.statusBar().showMessage(self.str['status_backup_created'].format(file_path))
                QMessageBox.information(self, self.str['info_title'], f"Бэкап сохранён:\n{file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'], f"Не удалось создать бэкап:\n{e}")
            self.statusBar().showMessage(self.str['status_backup_failed'].format(e))
            return False

    def update_save_button(self):
        if self.modified:
            self.btn_save.setEnabled(True)
            self.btn_save.setStyleSheet(self.button_style() + """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #8a3a2a, stop:1 #5a2a1a);
                    border-color: #aa5a4a;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #9a4a3a, stop:1 #6a3a2a);
                }
            """)
        else:
            self.btn_save.setEnabled(False)
            self.btn_save.setStyleSheet(self.button_style() + """
                QPushButton {
                    background: #3a2f22;
                    color: #7a6a5a;
                    border: 1px solid #4a3a2a;
                }
            """)

    def on_list_changed(self):
        self.check_if_modified()

    def on_current_mod_changed(self, current, previous):
        if current and (current.flags() & Qt.ItemIsSelectable):
            mod_name = current.data(Qt.UserRole + 3) or current.text()
            has_workshop = mod_name in self.workshop_ids
            if has_workshop:
                self.statusBar().showMessage(self.str['status_mod_selected_workshop'].format(mod_name))
            else:
                self.statusBar().showMessage(self.str['status_mod_selected_local'].format(mod_name))

    # ========== Запуск игры ==========
    def launch_game(self):
        if not self.kenshi_path:
            QMessageBox.warning(self, self.str['error_title'], "Путь к Kenshi не задан.")
            return

        game_exe = self.find_game_exe()
        if not game_exe:
            QMessageBox.warning(
                self,
                self.str['error_title'],
                f"Не найден исполняемый файл игры (kenshi_x64.exe / kenshi.exe) в папке:\n{self.kenshi_path}"
            )
            return

        try:
            game_folder = os.path.dirname(game_exe)

            clean_env = os.environ.copy()
            if hasattr(sys, '_MEIPASS'):
                if 'PATH_ORIG' in clean_env:
                    clean_env['PATH'] = clean_env['PATH_ORIG']
                clean_env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
                clean_env.pop('PYIDIE_VERBOSE', None)

            steam_exe = os.path.abspath(os.path.join(game_folder, "..", "..", "..", "steam.exe"))
            if not os.path.exists(steam_exe):
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
                    steam_install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    winreg.CloseKey(key)
                    steam_exe = os.path.join(steam_install_path, "steam.exe")
                except:
                    steam_exe = None

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            if steam_exe and os.path.exists(steam_exe):
                self.game_process = subprocess.Popen(
                    [steam_exe, "-applaunch", "233860"],
                    cwd=game_folder,
                    env=clean_env,
                    startupinfo=startupinfo,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                self.game_process = subprocess.Popen(
                    [game_exe],
                    cwd=game_folder,
                    env=clean_env,
                    startupinfo=startupinfo,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            self.statusBar().showMessage(self.str['status_game_launched'])
            self.close()

        except Exception as e:
            QMessageBox.critical(self, self.str['error_title'],
                                 self.str['error_launch_game'].format(e) + f"\n\nПуть: {game_exe}")

    def check_game_process(self):
        if self.game_process is None:
            return
        returncode = self.game_process.poll()
        if returncode is None:
            self.statusBar().showMessage(self.str['status_game_running'])
        else:
            if returncode != 0:
                QMessageBox.critical(
                    self,
                    self.str['error_title'],
                    f"Игра завершилась с ошибкой (код {returncode}).\n"
                    f"Часто это ошибка «No available renderers».\n"
                    f"Проверьте, что запускаете именно kenshi_x64.exe из папки игры."
                )
            else:
                QMessageBox.information(
                    self,
                    self.str['info_title'],
                    "Игра завершилась (код 0). Возможно, она сразу закрылась."
                )

    # ========== Контекстное меню ==========
    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item and (item.flags() & Qt.ItemIsSelectable):
            mod_name = item.data(Qt.UserRole + 3) or item.text()
            self.toggle_mod(mod_name)
            return

        menu = QMenu()
        action_refresh = menu.addAction(self.str['menu_refresh'])
        action_refresh.triggered.connect(self.load_mods_with_confirm)
        menu.addSeparator()
        action_manual = menu.addAction(self.str['menu_manual_paths'])
        action_manual.triggered.connect(self.manual_paths)
        action_launch = menu.addAction(self.str['btn_launch'])
        action_launch.triggered.connect(self.launch_game)
        menu.exec_(self.list_widget.mapToGlobal(pos))

    # ========== Переключение мода ==========
    def toggle_mod(self, mod_name):
        current = self.mod_status.get(mod_name, False)
        new_status = not current
        self.mod_status[mod_name] = new_status

        current_row = -1
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                stored = item.data(Qt.UserRole + 3) or item.text()
                if stored == mod_name:
                    current_row = i
                    break
        if current_row == -1:
            return

        item = self.list_widget.takeItem(current_row)

        if new_status:
            insert_pos = -1
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() in ("Включенные моды", "Enabled mods"):
                    insert_pos = i + 1
                    while insert_pos < self.list_widget.count():
                        next_item = self.list_widget.item(insert_pos)
                        if not (next_item.flags() & Qt.ItemIsSelectable):
                            break
                        next_mod = next_item.data(Qt.UserRole + 3) or next_item.text()
                        if self.mod_status.get(next_mod, False):
                            insert_pos += 1
                        else:
                            break
                    break
            if insert_pos == -1:
                insert_pos = 0
            self.list_widget.insertItem(insert_pos, item)
        else:
            insert_pos = -1
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() in ("Выключенные моды", "Disabled mods"):
                    j = i + 1
                    while j < self.list_widget.count():
                        cur_item = self.list_widget.item(j)
                        if not (cur_item.flags() & Qt.ItemIsSelectable):
                            break
                        cur_mod = cur_item.data(Qt.UserRole + 3) or cur_item.text()
                        if cur_mod.lower() > mod_name.lower():
                            insert_pos = j
                            break
                        j += 1
                    if insert_pos == -1:
                        insert_pos = j
                    break
            if insert_pos == -1:
                insert_pos = self.list_widget.count()
            self.list_widget.insertItem(insert_pos, item)

        item.setIcon(IconFactory.create_check_icon() if new_status else IconFactory.create_cross_icon())
        self.update_conflict_highlights()
        self.check_if_modified()
        enabled_count = sum(self.mod_status.values())
        status_word = self.str['mod_status_enabled'] if new_status else self.str['mod_status_disabled']
        self.statusBar().showMessage(
            self.str['status_mod_toggled'].format(mod_name, status_word, enabled_count)
        )

    def button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #5a4534, stop:1 #3c2f22);
                border: 1px solid #6b5a4a;
                border-radius: 4px;
                padding: 6px 14px;
                color: #e8d5b5;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #6b5a4a, stop:1 #4a3a2a);
            }
            QPushButton:pressed {
                background: #2a1f15;
            }
        """

    # ========== ЛОКАЛИЗОВАННЫЙ QUESTION ==========
    def _question_box(self, title, text):
        """Возвращает True, если пользователь нажал «Да», иначе False."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        btn_yes = msg.addButton(self.str['yes'], QMessageBox.YesRole)
        btn_no = msg.addButton(self.str['no'], QMessageBox.NoRole)
        msg.setDefaultButton(btn_yes)
        msg.exec_()
        return msg.clickedButton() == btn_yes

    # ========== Проверка обновлений ==========
    def check_for_updates(self):
        """Проверяет наличие обновлений на GitHub."""
        exe_path = sys.argv[0]
        current_version = get_file_version(exe_path)
        if current_version is None:
            return

        self.manager = QNetworkAccessManager()
        url = QUrl("https://api.github.com/repos/p4vl0-dev/kenshi-simple-mod-manager/releases/latest")
        request = QNetworkRequest(url)
        reply = self.manager.get(request)

        def handle_reply():
            if reply.error() == QNetworkReply.NoError:
                data = reply.readAll().data().decode('utf-8')
                try:
                    release = json.loads(data)
                    latest_tag = release.get('tag_name', '')
                    if latest_tag.startswith('v'):
                        latest_tag = latest_tag[1:]
                    if latest_tag and compare_versions(latest_tag, current_version) > 0:
                        self.show_update_dialog(latest_tag)
                except Exception:
                    pass
            reply.deleteLater()

        reply.finished.connect(handle_reply)

    def show_update_dialog(self, latest_version):
        """Показывает диалог о доступном обновлении."""
        msg = QMessageBox(self)
        msg.setWindowTitle(self.str['update_available_title'])
        msg.setText(self.str['update_available_text'].format(version=latest_version))
        btn_yes = msg.addButton(self.str['yes'], QMessageBox.YesRole)
        btn_no = msg.addButton(self.str['no'], QMessageBox.NoRole)
        msg.setDefaultButton(btn_yes)
        msg.exec_()
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
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    for ico in ["ksmm.ico", "ksmm.png"]:
        path = os.path.join(base, "icons", ico)
        if os.path.exists(path):
            icon_path = path
            break
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet("""
        QMessageBox, QFileDialog, QInputDialog, QFontDialog, QColorDialog {
            background: #1e160e;
            color: #e8d5b5;
        }
        QMessageBox QPushButton, QFileDialog QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #5a4534, stop:1 #3c2f22);
            border: 1px solid #6b5a4a;
            border-radius: 4px;
            padding: 6px 14px;
            color: #e8d5b5;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover, QFileDialog QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #6b5a4a, stop:1 #4a3a2a);
        }
        QMessageBox QPushButton:pressed, QFileDialog QPushButton:pressed {
            background: #2a1f15;
        }
        QMessageBox QLabel {
            color: #e8d5b5;
        }
        QFileDialog QListView, QFileDialog QTreeView {
            background: #2a1f15;
            color: #e8d5b5;
            border: 1px solid #4a3a2a;
        }
        QFileDialog QLineEdit {
            background: #2a1f15;
            color: #e8d5b5;
            border: 1px solid #4a3a2a;
            padding: 4px;
        }
        QFileDialog QComboBox {
            background: #2a1f15;
            color: #e8d5b5;
            border: 1px solid #4a3a2a;
        }
        QFileDialog QToolButton {
            background: transparent;
            color: #e8d5b5;
        }
    """)

    window = ModManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()