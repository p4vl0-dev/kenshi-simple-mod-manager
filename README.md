# Kenshi Simple Mod Manager

**A simple yet powerful mod manager for Kenshi with Steam Workshop support and a convenient user interface.**

![Kenshi Mod Manager](icons/ksmm.ico)

## 🎯 What is it?

**Kenshi Simple Mod Manager** is a desktop application for managing mods in the game Kenshi. It completely replaces the standard launcher, providing a much more convenient and informative interface for enabling/disabling mods and changing load order.

## ⚡ Features

- **Full control over mods**
  - Enable and disable mods with a single click (right-click on a mod → instant status toggle)
  - Drag-and-drop for convenient reordering of load order within the "Enabled" and "Disabled" lists
  - Save the modified list to `mods.cfg` with the option to automatically create a backup

- **Steam Workshop integration**
  - Automatic scanning of installed mods from the Workshop folder `workshop/content/233860`
  - Displays the mod's real name from the `.info` file (if available) alongside the `.mod` filename
  - Quick navigation to the mod's Steam Workshop page by clicking the Steam icon

- **Backup and restore**
  - Manually create a backup of the `mods.cfg` file to any chosen location on disk
  - Automatically create a timestamped backup when selecting the "Save with backup" option

- **Search and navigation**
  - Quick mod search by filename or by name from the `.info` file, with match highlighting
  - Convenient ▲▼ buttons for quick navigation through search results in the list

- **Localization**
  - Full support for Russian and English languages with instant switching via a button in the top right corner

- **Full diagnostics**
  - A separate diagnostics window showing exact paths to the game, total mod count, detected duplicates, and errors

## 📥 Installation

### Precompiled executable (Recommended)

1. Go to the [Releases](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/releases) page
2. Download the latest version of the `KenshiSimpleModManager.exe` file
3. Place the downloaded file in any convenient folder on your computer (it does not have to be in the game's root folder)
4. Run `KenshiSimpleModManager.exe`

> **Important:** On first launch, the program will try to find the Kenshi folder automatically via the Steam registry and standard disk paths. If auto-detection fails, you can specify the game path manually via the menu **View → Set Kenshi Path**.

## 🔧 Building from source

### System requirements
- Python 3.6 or higher
- PyQt5 library
- PyInstaller library

### Build instructions
1. Clone the repository to your computer:
   ```bash
   git clone https://github.com
   cd kenshi-simple-mod-manager
   ```
2. Install the required libraries:
   ```bash
   pip install PyQt5
   pip install pyinstaller
   ```
3. Make sure the `icons` folder (with interface icons) and `fonts` folder (with fonts) are located in the project root and contain all the necessary resource files.
4. Run the build command to compile the executable:
   ```bash
   pyinstaller --onefile --windowed --clean --name KenshiSimpleModManager --icon=icons/ksmm.ico --version-file=version.txt --add-data "icons;icons" --add-data "fonts;fonts" kenshi_simple_mod_manager.py
   ```
Once the process is complete, the ready-to-use `KenshiSimpleModManager.exe` file will appear in the newly created `dist/` folder.

## 📁 Project structure

```text
kenshi-simple-mod-manager/
├── kenshi_simple_mod_manager.py   # Main application script
├── icons/                         # Interface icons and graphic resources
│   ├── ksmm.ico                   # Main application icon
│   ├── steam_tray.ico             # Steam icon
│   ├── folder.webp                # Folder icon (local mods)
│   ├── warning.webp               # Warning icon (errors/duplicates)
│   └── github.webp                # GitHub icon
├── fonts/                         # Custom fonts (optional)
│   └── Exo2-Bold.ttf
└── README.md
```

## 📜 License

This project is distributed under the free MIT license.

## 🛠️ Support and feedback

If you found a bug, encountered an error, or want to suggest a new feature, please create an [Issue](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/issues) in the project repository.
