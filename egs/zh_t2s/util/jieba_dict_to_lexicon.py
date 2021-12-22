''' convert jieba dictionary to nnlp lexicon format '''
import sys

if len(sys.argv) != 3:
    print('Usage: jieba_dict_to_lexicon.py <jieba-dict> <nnlp-lexicon>')
    sys.exit(1)

input_dict = sys.argv[1]
output_lexicon = sys.argv[2]

freq = {}
with open(input_dict, encoding='utf-8') as f:
    for line in f:
        row = line.strip().split()
        word = row[0]
        count = int(row[1])
        freq[word] = count

total_count = sum(freq.values())

with open(output_lexicon, 'w', encoding='utf-8') as f:
    for word, count in freq.items():
        f.write(f'{word} {count / total_count:.5g} {" ".join(list(word))}\n')
