import sys

from .cli import add_selfloop_cli, add_symbol_cli, build_lexicon_fst, remove_disambig


def print_usage_and_exit() -> None:
    print('Usage: python3 -m nnlp <command> [args]')
    print('commands:')
    print('    buildlexfst: build lexicon FST from text file')
    print('    rmdisambig: remove disambig symbols from FST or symbol file')
    print('    addselfloop: add selfloop to FST')
    print('    addsymbol: add symbol to symbol file')

    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_usage_and_exit()

    cmd = sys.argv[1]
    if cmd == 'buildlexfst':
        build_lexicon_fst(sys.argv[2:])
    elif cmd == 'rmdisambig':
        remove_disambig(sys.argv[2:])
    elif cmd == 'addselfloop':
        add_selfloop_cli(sys.argv[2:])
    elif cmd == 'addsymbol':
        add_symbol_cli(sys.argv[2:])
    else:
        raise Exception(f'unexpected command: {cmd}')
