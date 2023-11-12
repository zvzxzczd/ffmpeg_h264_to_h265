import re

file_name = input("请输入文件路径：")

re_name = re.sub(r"\\", r"/", file_name)
print(re_name)

video_coding = [
    "WMV2",
    "VP8",
    "VC-1",
    "AVC",
    "AV1",
    "HEVC",
    "RealVideo 4",
    "VP9",
    "JPEG",
    "MPEG Video",
    "MPEG-4 Visual"
]
b = []
for i in video_coding:
    b.append(i.lower())
# print(b)
