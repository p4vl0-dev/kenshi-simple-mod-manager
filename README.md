# Kenshi Simple Mod Manager

A simple mod manager for the game Kenshi. Features:
- Enable/disable mods.
- Change load order by drag-and-drop.
- Save load profiles.
- Open mod pages in Steam Workshop.
- Create backups of `mods.cfg`.

## Installation
Download the [latest release](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/releases) and run `KenshiSimpleModManager.exe`.

## Building from source
1. Install dependencies:
   ```
   pip install PyQt5
   pip install pyinstaller
   ```
   (You may also install specific versions if needed, e.g., `PyQt5==5.15.9`)

2. Run the build command:  
   ```
   pyinstaller --onefile --windowed --name="KenshiSimpleModManager" --icon="icons/ksmm.ico" --add-data "icons;icons" --add-data "fonts;fonts" kenshi_simple_mod_manager.py
   ```

## License
MIT

---

# Kenshi Simple Mod Manager (Русский)

Простой менеджер модов для игры Kenshi. Возможности:
- Включать/выключать моды.
- Менять порядок загрузки перетаскиванием.
- Сохранять профили загрузки.
- Открывать страницы модов в Steam Workshop.
- Создавать бэкапы `mods.cfg`.

## Установка
Скачайте [последний релиз](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/releases) и запустите `KenshiSimpleModManager.exe`.

## Сборка из исходников
1. Установите зависимости:
   ```
   pip install PyQt5
   pip install pyinstaller
   ```
   (При необходимости можно указать конкретные версии, например `PyQt5==5.15.9`)

2. Выполните команду сборки:  
   ```
   pyinstaller --onefile --windowed --name="KenshiSimpleModManager" --icon="icons/ksmm.ico" --add-data "icons;icons" --add-data "fonts;fonts" kenshi_simple_mod_manager.py
   ```

## Лицензия
MIT
