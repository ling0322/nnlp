#!/usr/bin/env python3

from nnlp import Fst, Segmenter

fst = Fst.from_json('exp/wordseg.json')
segmenter = Segmenter(fst)
assert segmenter.segment_string('南京市长江大桥') == ['南京市', '长江大桥']
assert segmenter.segment_string('研究生命的起源') == ['研究', '生命', '的', '起源']
assert segmenter.segment_string('女朋友很重要吗') == ['女朋友', '很', '重要', '吗']
assert segmenter.segment_string('北京大学生前来应聘') == ['北京', '大学生', '前来', '应聘']
assert segmenter.segment_string('长春市长春药店') == ['长春市', '长春', '药店']
assert segmenter.segment_string('你好hello你好现在是北京时间早上8点20左右') == ['你好', 'hello', '你好', '现在', '是', '北京', '时间', '早上', '8', '点', '20', '左右']
assert segmenter.segment_string('嗨hello你好 world\t1.0a\tiPhone10\n\n\r22\n') == ['嗨', 'hello', '你好', 'world', '1.0a', 'iPhone10', '22']
