# Kenshi Simple Mod Manager

Простой менеджер модов для Kenshi на PyQt5: находит игру, Workshop и `mods.cfg`
автоматически, показывает единый список локальных и Workshop-модов,
позволяет включать/выключать их и менять порядок перетаскиванием.

## Возможности

- Автопоиск папки Kenshi, папки Workshop (`steamapps/workshop/content/233860`) и `mods.cfg`
- Единый список: локальные моды (`mods/`) + подписки Workshop, с объединением дублей
- Включение/выключение мода кликом, перетаскивание для смены порядка загрузки
- Поиск мода по имени/заголовку (стрелки ▲/▼ - переход между совпадениями)
- Подсветка модов с отсутствующей или неверно упорядоченной зависимостью -
  при необходимости отключается константой `ENABLE_DEPENDENCY_WARNINGS`
  в самом начале `kenshi_simple_mod_manager.py`
- Обнаружение дублей одного мода (например, установлен и локально, и через Workshop)
- Бэкап `mods.cfg` перед сохранением (автоматический и вручную через меню «Файл»)
- Быстрое обновление списка модов по F5
- Переключение языка интерфейса RU/EN одной кнопкой
- Запуск игры прямо из менеджера

## Запуск из исходников

```bash
python -m pip install PyQt5
python kenshi_simple_mod_manager.py
```

## Сборка .exe

Зависимости для сборки: `PyQt5` и `pyinstaller`.

```bash
python -m pip install PyQt5 pyinstaller
```

Сама сборка - одной командой:

```bash
pyinstaller --onefile --windowed --name="KenshiSimpleModManager" --icon="icons/ksmm.ico" --add-data "icons;icons" --add-data "fonts;fonts" --upx-dir "C:\upx" --strip --exclude-module PyQt5.QtSql --exclude-module PyQt5.QtNetwork --exclude-module PyQt5.QtWebEngineWidgets --exclude-module PyQt5.QtWebKitWidgets --exclude-module PyQt5.QtPrintSupport --exclude-module PyQt5.QtXml --exclude-module PyQt5.QtSvg --exclude-module PyQt5.QtOpenGL --exclude-module PyQt5.QtMultimedia --exclude-module PyQt5.QtTest --exclude-module PyQt5.QtQuick --exclude-module PyQt5.QtQml kenshi_simple_mod_manager.py
```

Готовый `.exe` появится в папке `dist`.

Если `upx` не установлен (или не нужен), просто уберите `--upx-dir "C:\upx" --strip`
из команды - сборка сработает и без него, просто .exe будет чуть крупнее.

> Команду можно выполнить как в обычном терминале (cmd), так и запустить прямо
> из VS Code через встроенный терминал (`` Ctrl+` ``) - никаких task-файлов
> для этого не нужно, это обычная консольная команда.

## Структура проекта

```
kenshi_simple_mod_manager.py   # основной файл менеджера
icons/                         # ksmm.ico, ksmm.png и иконки интерфейса
fonts/                         # Kenshi.ttf, Exo2-Bold.ttf (опционально)
README.md
LICENSE
```

## Известные ограничения

Разбор зависимостей мода читается напрямую из бинарного `.mod` файла
(реверс-инжиниринг формата, официальной документации нет). В редких случаях
это может дать ложное срабатывание. Если это мешает - отключите константу
`ENABLE_DEPENDENCY_WARNINGS` вверху файла.

## Проект

<https://github.com/p4vl0-dev/kenshi-simple-mod-manager>
