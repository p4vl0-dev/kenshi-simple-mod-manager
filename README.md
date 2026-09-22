# Kenshi Simple Mod Manager

**A simple yet powerful mod manager for Kenshi with Steam Workshop support and a convenient user interface.**

![Kenshi Mod Manager](icons/ksmm.ico)

## 🎯 What is it?

**Kenshi Simple Mod Manager** is a desktop application for managing mods in the game Kenshi. It completely replaces the standard launcher, providing a much more convenient and informative interface for enabling/disabling mods and changing load order.

## ⚡ Features

### 🎛 Full control over mods

- **Enable / disable mods with a single right-click** — instant status toggle.
- **Multi-select** with `Shift` / `Ctrl` + left click to operate on a group of mods at once.
- **Batch toggle** — right-click on a multi-selection to enable or disable all selected mods in one action.
- **Drag & drop reordering** inside the "Enabled" section to control the exact load order.
- **Cross-section dragging** — dragging a mod from "Disabled" to "Enabled" (or vice versa) automatically toggles its status:
  - When moving to "Enabled", the mod is inserted at the drop position.
  - When moving to "Disabled", the section is kept in alphabetical order.
- **Auto-scroll** while dragging near the edges of the list for long mod collections.
- **Only mods containing a `.mod` file are shown** — empty folders are ignored.
- **Save the modified list to `mods.cfg`** with the option to automatically create a backup (timestamped or to a chosen location).
- The **Save** button is highlighted when there are unsaved changes and stays disabled otherwise.

### 🔍 Search and navigation

- **Instant search** by mod filename or by the real name from the `.info` file.
- **Match highlighting** with auto-scroll to the first result.
- **▲ ▼ navigation buttons** to quickly jump between matches up and down.
- **Clear button** (cross icon) built into the search field.

### 🖼 Mod hover cards

- **Hover cards** appear when the cursor stays over a mod name for a configurable delay.
- For **Steam Workshop mods**, the card shows the actual image, title, and description fetched from the Steam Web API.
- **Click the image or title** to open the mod's Workshop page in your browser.
- For **local mods**, the card shows the file name and any detected conflict information.
- **Configurable** — hover cards can be disabled entirely or their delay can be tuned in Settings.

### 🌐 Steam Workshop integration

- **Automatic scanning** of mods from the Workshop folder `workshop/content/233860`.
- **Displays the mod's real name** from the `.info` file (when available) alongside the `.mod` filename.
- **Steam icon next to Workshop mods** — click it to open the mod's page in the Steam Workshop.
- **Folder icon next to local mods** — click it to open the mod's folder in Explorer.
- **Duplicate detection** — a warning icon appears next to mods that exist in both local and Workshop folders; click it to see all copies and open the one you want.

### 🧩 Dependency & conflict checks

- **Automatic dependency validation** of the enabled list.
- **Conflict highlighting** — mods with missing or out-of-order dependencies are highlighted in the list.
- Tooltip on the highlighted entry explains exactly what's wrong.

### 💾 Backup and restore

- **Manually save `mods.cfg`** to any location on disk (also useful as a "profile" save).
- **Automatic backup** on saving with the "Save with backup" option.
- **Load a temporary list from any `.cfg` file** without touching the game folder — perfect for testing different load orders.
- The **name of the last loaded config** is shown in the window title and in Settings.

### ⚙️ Settings

- **Interface language** — full Russian and English localization with instant switching via the button in the top-right corner.
- **Hover cards** — enable/disable and set the appearance delay.
- **Close manager after launching the game** — useful for testing.
- **Kenshi path** — change the game folder manually if auto-detection fails.

### 🚀 Additional

- **One-click game launch** — starts Kenshi directly or through Steam (`-applaunch 233860`), hiding the console window.
- **Auto-detection** of the Kenshi installation via the Steam registry and common disk paths.
- **Full diagnostics** — the status bar and Settings window show the exact paths to the game, `mods.cfg`, and the Workshop folder.
- **Auto-update check** — the app checks GitHub for a new release on startup and offers to open the download page.
- **GitHub button** in the menu bar for quick access to the project page.
- **Sandboxed look & feel** — a dark sandy theme with custom fonts and icons matching the Kenshi aesthetic.

## 📥 Installation

### Precompiled executable (Recommended)

1. Go to the [Releases](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/releases) page.
2. Download the latest version of the `KenshiSimpleModManager.exe` file.
3. Place the downloaded file in any convenient folder on your computer (it does not have to be in the game's root folder).
4. Run `KenshiSimpleModManager.exe`.

> **Important:** On first launch, the program will try to find the Kenshi folder automatically via the Steam registry and standard disk paths. If auto-detection fails, you can specify the game path manually via the menu **View → Settings → Kenshi path**.

## 🔧 Building from source

### System requirements

- Python 3.6 or higher
- PyQt5 library
- PyInstaller library

### Build instructions

1. Clone the repository to your computer:

```bash
git clone https://github.com/p4vl0-dev/kenshi-simple-mod-manager
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
├── kenshi_simple_mod_manager.py # Main application script
├── icons/                       # Interface icons and graphic resources
│   ├── ksmm.ico                # Main application icon
│   ├── steam_tray.ico          # Steam icon
│   ├── folder.webp             # Folder icon (local mods)
│   ├── warning.webp            # Warning icon (errors/duplicates)
│   └── github.webp             # GitHub icon
├── fonts/                       # Custom fonts (optional)
│   └── Exo2-Bold.ttf
└── README.md
```

## 📜 License

This project is distributed under the free MIT license.

## 🛠️ Support and feedback

If you found a bug, encountered an error, or want to suggest a new feature, please create an [Issue](https://github.com/p4vl0-dev/kenshi-simple-mod-manager/issues) in the project repository.
