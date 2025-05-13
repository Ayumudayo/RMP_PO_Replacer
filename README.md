# RMP PO Replacer

A simple command-line tool to translate(or replace) `msgstr` entries in `.po` file between Final Fantasy XIV language CSV mappings.

Created for [Re:MakePlace](https://github.com/RemakePlace/app) [Crowdin project](https://crowdin.com/project/re-makeplace).

## Features

-   Supports all languages in FFIXV(EN, JP, DE, FR) as source and target languages.
-   Strips `<Emphasis>` tags and normalizes case for matching.
-   Logs every replacement and warns on missing mappings.
-   Customizable CSV directory and language settings.

## Prerequisites

### Current FFXIV Version is `2025.04.16.0000.0000`

-   CSV files exported from FFXIV data:
    -   And name csv files like below.
    -   `Item_EN.csv`, `Item_JP.csv`, `Item_DE.csv`, `Item_FR.csv`
    -   Not all of 4 csv is needed. You can pick just two of them.

## Installation

Just clone this repository. That's it!

No any dependencies!

## Usage

Place your CSV files in a `csv/` directory, named `Item_EN.csv`, `Item_JP.csv`, etc.

It's only supposed to replace what's in `Item.csv`.

I'm content with just getting the item name right, I don't really care about the name of the painting, etc.
Feel free to modify it to support those if you want and give some PR.

```bash
# Default: translate English → Japanese
python replace.py AssetName.po
# Explicit source/target, e.g. German → French
python replace.py AssetName.po AssetName.fr.po --src de --tgt fr
# Specify a different CSV folder
python replace.py --csv-dir ./data/csv AssetName.po
```

### Command-line Options

```
usage: replace.py [-h] [--csv-dir CSV_DIR] [--src {en,jp,de,fr}] [--tgt {en,jp,de,fr}] po_in [po_out]

Translate .po entries between FF14 languages (EN, JP, DE, FR).

positional arguments:
  po_in                Input .po file
  po_out               Output .po file (default: po_in with target code)

options:
  -h, --help           show this help message and exit
  --csv-dir CSV_DIR    Directory containing Item_<lang>.csv files (default: csv)
  --src {en,jp,de,fr}  Source language code (default: en)
  --tgt {en,jp,de,fr}  Target language code (default: jp)
```

## Logging

All operations, replacements, warnings, and summary statistics are written to `replace.log` in the current directory, and also printed to the console.

On every run, `replace.log` will be cleared and rewritten.

## Example

Before:

```po
msgid "Fire Shard"
msgstr ""
```

After running script:

```po
msgid "Fire Shard"
msgstr "ファイアシャード"  # (example Japanese translation)
```

## License

MIT License.
