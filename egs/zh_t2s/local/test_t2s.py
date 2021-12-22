from nnlp import Fst, Converter

fst = Fst.from_json('exp/zh_t2s.json')
converter = Converter(fst)
assert converter.convert_string('肯德基要點的是原始的薄皮嫩雞') == '肯德基要点的是原始的薄皮嫩鸡'
assert converter.convert_string('一堆人吃辣的卡拉雞，那個才不是經典') == '一堆人吃辣的卡拉鸡，那个才不是经典'
assert converter.convert_string('薄皮嫩雞裹粉多汁，好餓…') == '薄皮嫩鸡裹粉多汁，好饿…'
assert converter.convert_string('然後漢堡王要點是薯球，其他都不行，漢堡說實在也還好') == '然后汉堡王要点是薯球，其他都不行，汉堡说实在也还好'
assert converter.convert_string('摩斯要點的是紅茶，漢堡他經典好吃的品項都下架了') == '摩斯要点的是红茶，汉堡他经典好吃的品项都下架了'
assert converter.convert_string('麥當勞越漲越貴，還有人說便宜，真TM笑死') == '麦当劳越涨越贵，还有人说便宜，真TM笑死'
assert converter.convert_string('沙烏地阿拉伯或譯') == '沙特阿拉伯或译'
assert converter.convert_string('波士尼亞赫塞哥維') == '波士尼亚赫塞哥维'
