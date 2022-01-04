#!/usr/bin/env python3

''' convert jieba dictionary to nnlp lexicon format '''
import sys

freq = {}
for line in sys.stdin:
    row = line.strip().split()
    word = row[0]
    count = int(row[1])
    freq[word] = count

total_count = sum(freq.values())

for word, count in freq.items():
    sys.stdout.write(f'{word} {count / total_count:.5g} {" ".join(list(word))}\n')