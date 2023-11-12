import json

with open("./转码缓存/输出/json_data/转码数据.json", "r", encoding="utf-8") as jw:
    转码数据 = json.load(jw)

with open("./转码缓存/输出/json_data/筛选数据.json", "r", encoding="utf-8") as jw:
    匹配文件 = json.load(jw)

dict_输出 = {"支持的格式": [], "未转码": [], "已完成": [], "转码失败": [], "不支持编码": [], "转码损失过大": [],
             "读取编码信息失败": [], "转码文件超大": [], "不支持格式": [], }

for k, v in 转码数据.items():
    if v == 0:
        dict_输出["未转码"].append(k)
    if v == 1:
        dict_输出["已完成"].append(k)
    if v == 2:
        dict_输出["转码失败"].append(k)
    if v == 3:
        dict_输出["不支持编码"].append(k)
    if v == 4:
        dict_输出["转码损失过大"].append(k)
    if v == 5:
        dict_输出["读取编码信息失败"].append(k)
    if v == 6:
        dict_输出["转码文件超大"].append(k)
try:
    for k, v in 匹配文件["支持的格式"].items():
        dict_输出["支持的格式"] += v
except:
    dict_输出["支持的格式"] = []
try:
    for k, v in 匹配文件["不支持格式"].items():
        dict_输出["不支持格式"] += v
except:
    dict_输出["不支持格式"] = []

with open("./转码缓存/输出/json_data/整理数据.json", "w", encoding="utf-8") as jw:
    json.dump(dict_输出, jw, indent=4, ensure_ascii=False)