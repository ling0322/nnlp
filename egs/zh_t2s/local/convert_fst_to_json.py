from nnlp import Fst
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-fst', help='input text format FST file')
parser.add_argument('-ilabel', help='input symbol file')
parser.add_argument('-olabel', help='output symbol file')
parser.add_argument('-output_json', help='output symbol file')
cmd_args = parser.parse_args()

with open(cmd_args.ilabel, encoding='utf-8') as f_isym, \
     open(cmd_args.olabel, encoding='utf-8') as f_osym, \
     open(cmd_args.fst, encoding='utf-8') as f_fst, \
     open(cmd_args.output_json, 'w', encoding='utf-8') as f_json:
    fst = Fst.from_text(f_isym, f_osym, f_fst)
    fst.to_json(f_json)
