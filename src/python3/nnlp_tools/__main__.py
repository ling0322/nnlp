import sys

from .cli import build_lexicon_fst, remove_disambig


def print_usage_and_exit() -> None:
    print('Usage: python3 -m nnlp <command> [args]')
    print('commands:')
    print('    build_lexicon_fst: build lexicon FST from text file')

    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_usage_and_exit()

    cmd = sys.argv[1]
    if cmd == 'build_lexicon_fst':
        build_lexicon_fst(sys.argv[2:])
    elif cmd == 'rm_disambig':
        remove_disambig(sys.argv[2:])
