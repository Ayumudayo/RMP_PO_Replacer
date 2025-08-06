import csv
import re
import os
import sys
import argparse
import logging
import time


def normalize(text: str) -> str:
    """Strip HTML tags, punctuation, and lowercase for matching."""
    text = re.sub(r'<[^>]+>', '', text)  # Strip tags
    text = re.sub(r'[\"\',.?!:;()]|', '', text)  # Strip punctuation
    return text.strip().lower()


def load_mapping(csv_path: str, key_col: str, val_cols: list[str], normalize_key=False) -> dict:
    """
    Load a CSV mapping:
      - If normalize_key is True: map normalized val_col -> key_col for each val_col in val_cols
      - Else: map key_col -> first val_col
    Skips first three header lines.
    """
    mapping = {}
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        cols = next(reader)
        names = next(reader)
        next(reader)
        key_idx = cols.index(key_col)
        val_idxs = [names.index(v) for v in val_cols]
        for row in reader:
            if len(row) <= max(key_idx, *val_idxs):
                continue
            item_id = row[key_idx].strip('"')
            if not item_id:
                continue
            if normalize_key:
                for val_idx in val_idxs:
                    name = row[val_idx].strip('"')
                    if name:
                        mapping[normalize(name)] = item_id
            else:
                name = row[val_idxs[0]].strip('"')
                if name:
                    mapping[item_id] = name
    return mapping


def translate(po_in: str, po_out: str, eng_map: dict, id_map: dict, src: str, tgt: str):
    """
    Replace empty msgstr in .po using eng_map and id_map, logging each action.
    """
    start = time.time()
    total = replaced = 0
    missing = []
    logging.info(f"Translating {src.upper()}→{tgt.upper()}: '{po_in}'→'{po_out}'")
    with open(po_in, encoding='utf-8') as fin, open(po_out, 'w', encoding='utf-8') as fout:
        msgid = None
        for line in fin:
            if line.startswith('msgid '):
                match = re.match(r'msgid\s+\"(.*)\"', line)
                msgid = match.group(1) if match else None
                fout.write(line)
                continue
            if msgid and line.strip() == 'msgstr ""':
                total += 1
                item_id = eng_map.get(normalize(msgid))
                tgt_name = id_map.get(item_id, '') if item_id else ''
                if tgt_name:
                    fout.write(f'msgstr "{tgt_name}"\n')
                    replaced += 1
                    logging.info(f"Replaced '{msgid}'→'{tgt_name}' (ID={item_id})")
                else:
                    fout.write(line)
                    missing.append(msgid)
                    logging.warning(f"No mapping for '{msgid}'")
                msgid = None
                continue
            fout.write(line)
    elapsed = time.time() - start
    logging.info(f"Processed {total} entries, {replaced} replacements in {elapsed:.2f}s")
    if missing:
        logging.info(f"Missing mappings for {len(missing)} entries.")


def main():
    parser = argparse.ArgumentParser(
        description="Translate .po entries between FF14 languages (EN, JP, DE, FR)",
        add_help=False)
    # custom help
    parser.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    parser.add_argument('po_in', nargs='?', help='Input .po file')
    parser.add_argument('po_out', nargs='?', help='Output .po file (default: *.X.po)')
    parser.add_argument('--csv-dir', default='csv', help='Directory of Item_<lang>.csv files')
    parser.add_argument('--src', choices=['en','jp','de','fr'], default='en', help='Source language (default: en)')
    parser.add_argument('--tgt', choices=['en','jp','de','fr'], default='jp', help='Target language (default: jp)')

    # override error to show help
    def custom_error(message):
        sys.stderr.write(f"Error: {message}\n\n")
        parser.print_help()
        sys.exit(2)
    parser.error = custom_error

    # print help if no args
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.src == args.tgt:
        parser.error(f"Source ({args.src}) and target ({args.tgt}) languages must differ.")

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.FileHandler('replacer.log', 'w', 'utf-8'), logging.StreamHandler()])
    logging.info('=== Script Start ===')

    # determine file names
    try:
        en_csv = os.path.join(args.csv_dir, f'Item_{args.src.upper()}.csv')
        tgt_csv = os.path.join(args.csv_dir, f'Item_{args.tgt.upper()}.csv')
    except FileNotFoundError as e:
        logging.error(f"Can't find CSV file: {e.filename}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error has occurred while loading the map.: {e}")
        sys.exit(1)
    out_po = args.po_out or args.po_in.replace('.po', f'.{args.tgt}.po')

    # load mappings
    try:
        eng_map = load_mapping(en_csv, 'key', ['Singular', 'Name'], normalize_key=True)
        id_map = load_mapping(tgt_csv, 'key', ['Name'], normalize_key=False)
    except Exception as e:
        logging.error(f"Error has occurred while loading the map.: {e}")
        sys.exit(1)
    logging.info(f"Loaded {len(eng_map)} {args.src}->ID, {len(id_map)} ID->{args.tgt}")

    try:
        translate(args.po_in, out_po, eng_map, id_map, args.src, args.tgt)
    except Exception as e:
        logging.exception("An unexpected error has occurred during translation.")
        sys.exit(1)
    logging.info('=== Script End ===')

if __name__ == '__main__':
    main()