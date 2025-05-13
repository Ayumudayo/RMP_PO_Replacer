import csv
import re
import os
import sys
import argparse
import logging
import time


def normalize(text: str) -> str:
    """Strip <Emphasis> tags and lowercase for matching."""
    return re.sub(r'</?Emphasis>', '', text).strip().lower()


def load_mapping(csv_path: str, key_col: str, val_col: str, normalize_key=False) -> dict:
    """
    Load a CSV mapping:
      - If normalize_key is True: map normalized val_col -> key_col
      - Else: map key_col -> val_col
    Skips first three header lines.
    """
    mapping = {}
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        cols = next(reader)
        names = next(reader)
        next(reader)
        key_idx = cols.index(key_col)
        val_idx = names.index(val_col)
        for row in reader:
            if len(row) <= max(key_idx, val_idx):
                continue
            item_id = row[key_idx].strip('"')
            name = row[val_idx].strip('"')
            if not item_id or not name:
                continue
            if normalize_key:
                mapping[normalize(name)] = item_id
            else:
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
                msgid = re.match(r'msgid\s+"(.*)"', line).group(1)
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

    # print help if no args or invalid usage
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    # override error to show help
    def error(msg):
        sys.stderr.write(f"Error: {msg}\n\n")
        parser.print_help()
        sys.exit(2)
    parser.error = error

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.FileHandler('replacer.log', 'w', 'utf-8'), logging.StreamHandler()])
    logging.info('=== Script Start ===')

    # determine file names
    en_csv = os.path.join(args.csv_dir, f'Item_{args.src.upper()}.csv')
    tgt_csv = os.path.join(args.csv_dir, f'Item_{args.tgt.upper()}.csv')
    out_po = args.po_out or args.po_in.replace('.po', f'.{args.tgt}.po')

    # load mappings
    eng_map = load_mapping(en_csv, 'key', 'Singular', normalize_key=True)
    id_map = load_mapping(tgt_csv, 'key', 'Name', normalize_key=False)
    logging.info(f"Loaded {len(eng_map)} {args.src}->ID, {len(id_map)} ID->{args.tgt}")

    translate(args.po_in, out_po, eng_map, id_map, args.src, args.tgt)
    logging.info('=== Script End ===')

if __name__ == '__main__':
    main()
