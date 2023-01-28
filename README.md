# Ffmpeg_h264_to_h265
h26转码为h265

Python环境为3.10

需自行配置安装FFmpeg

需要自行安装python3.10 和requirements.txt 中依赖

初始化文件夹须在 转码文件.py name 中修改以下三个变量的值：

```
read   # 对应要转码文件的文件或文件夹 
write  # 对应临时写缓存入的文件夹
loss   # 对应临时转码损失过大的文件保存文件夹，不覆盖源文件.

# write  loss  对应的文件夹如果没有，手动创建后，将路径设置到对应的变量中。
```

![image](https://github.com/zvzxzczd/ffmpeg_h264_to_h265/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-01-13%20005931.png)


创建 D:/Program_Files/转码配置/ 文件夹，该文件夹保存转码的日志数据 



 默认使用N卡编码加速，如需A卡、CPU编码，请自行修改：

```
# 修改：ffmpeg_run() 和 ffmpeg_run_nocopy() 函数 -c:v 后的参数
class Ffm_run:
    pass
    
    def ffmpeg_run(self):
    pass

    def ffmpeg_run_nocopy(self)::
    pass
    
# 将以上两个函数中-c:v hevc_nvenc   修改为你需要的编码器
# 或者将-c:v hevc_nvenc 直接修改为 -c:v libx265  使用CPU编码
```

![image](https://github.com/zvzxzczd/ffmpeg_h264_to_h265/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-01-13%20012320.png)
