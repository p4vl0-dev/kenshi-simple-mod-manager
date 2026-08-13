# Kenshi Simple Mod Manager

**A simple yet powerful mod manager for Kenshi with Steam Workshop support and a user-friendly interface.**

![Kenshi Mod Manager](icons/ksmm.ico)

## 🎯 What is this?

**Kenshi Simple Mod Manager** is a desktop application for managing mods in the game Kenshi. It replaces the standard launcher by providing a more convenient and informative interface for enabling/disabling mods, changing load order, checking conflicts, and working with mods from Steam Workshop.

## ⚡ Features

- **Full mod control**
  - Enable/disable mods (right-click on a mod → instant toggle)
  - Drag-and-drop to change load order within "Enabled" / "Disabled" sections
  - Save order to `mods.cfg` with optional backup before saving

- **Steam Workshop integration**
  - Automatically scans mods from `workshop/content/233860`
  - Displays mod title from `.info` file (if available) and `.mod` filename
  - Opens mod page in Workshop by clicking the Steam icon

- **Load profiles**
  - Save current enabled mod order to a separate `.cfg` file
  - Quick load of saved profile (temporary application without changing main `mods.cfg`)

- **Backup & restore**
  - Manual backup of `mods.cfg` to any location
  - Automatic backup with timestamp when choosing "Save with backup"

- **Search and navigation**
  - Quick search by mod name and by title from `.info` (highlight matches)
  - ▲▼ buttons to navigate through search results

- **Localization**
  - Russian and English languages (toggle button in top‑right corner)

- **Full diagnostics**
  - Diagnostic window with paths to game, number of mods, duplicates, etc.

- **Launch game**
  - One-click launch Kenshi via Steam (with authentication) or directly

## 📥 Installation

### Pre‑built binary (recommended)

1. Go to the [Releases page](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/releases)
2. Download `KenshiSimpleModManager.exe`
3. Place it in any folder (does not have to be next to the game)
4. Run `KenshiSimpleModManager.exe`

> **Important:** On first launch, the program will attempt to find Kenshi automatically (via Steam registry and standard paths). If it fails, you can manually set the path via **View → Set Kenshi path**.

## 🔧 Building from source

### Requirements
- Python 3.6+
- PyQt5
- PyInstaller

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/p4vl0-dev/kenshi-simple-mod-manager.git
   cd kenshi-simple-mod-manager
   ```
2. Install dependencies:
   ```bash
   pip install PyQt5
   pip install pyinstaller
   ```
3. Ensure that the icons and fonts folders are in the project root (containing the required files).
4. Build the executable:
   ```bash
   pyinstaller --onefile --windowed --clean --name KenshiSimpleModManager --icon=icons/ksmm.ico --version-file=version.txt --add-data "icons;icons" --add-data "fonts;fonts" kenshi_simple_mod_manager.py
   ```
The finished KenshiSimpleModManager.exe will appear in the dist folder.

## 📁 Project structure

```text
kenshi-simple-mod-manager/
├── kenshi_simple_mod_manager.py   # Main script
├── icons/                         # Icons for the interface
│   ├── ksmm.ico                   # Application icon
│   ├── steam_tray.ico             # Steam icon
│   ├── folder.webp                # Folder icon (local mods)
│   ├── warning.webp               # Warning icon (duplicates/errors)
│   └── github.webp                # GitHub icon
├── fonts/                         # Fonts (optional)
│   ├── Kenshi.ttf
│   └── Exo2-Bold.ttf
└── README.md
```

## 📜 License

This project is distributed under the MIT license.  
In short: you may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software without restriction, provided that the copyright notice is retained. See the LICENSE file for details.

## 🛠️ Support

If you find a bug or have a suggestion, create an [Issue](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/issues).
