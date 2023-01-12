# Ffmpeg_h264_to_h265
h26转码为h265

Python环境为3.10

需自行配置安装FFmpeg
需自行创建 D:/Program_Files/转码配置/ 文件夹，或者修改 r_json（） rw_no_type（）内文件路径

初始化文件夹须在 转码文件.py  __name__ 中修改以下三个变量的值：
read    # 读取
write   # 写缓存入
loss    # 转码损失过大
