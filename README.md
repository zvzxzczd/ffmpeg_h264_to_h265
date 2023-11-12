# Ffmpeg_h264_to_h265
h26转码为h265

Python环境为3.10

需自行配置安装FFmpeg

需要自行安装python3.10 和requirements.txt 中依赖

## 初始化文件夹
须在 转码文件.py 设置文件路径，并向 run_ff 方法传递要转码的文件路径：

```
test_dir = r"你的视频保存路径"  # 传入路径

传入文件夹参数，写入json数据
run_ff(y_dist=test_dir)

# json_w 可以不传递参数，默认将所有转码信息保存到本地 
# 不保存转码信息
json_w=True
```

![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-11-12%20153514.png)


## 预设多个转码信息
可在 run_ff 方法中，配置多个文件的快捷预设值，运行时 run_ff(预设值) 即可

![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-11-12%20140512.png)
```
run_ff(1)
# run_ff(x_value=1) 也可以运行
# 如上图及下图所示，直接转码预设的项目 “./视频 ” 文件夹的视频，转码信息保存在 “./视频/json_data/转码数据.json” 文件夹中

```

![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-11-12%20142918.png)
![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-11-12%20143143.png)

### 临时使用预设信息，但是转码视频为其他路径的情况
```
run_ff(x_value=1,read_folder="要转码的视频文件夹路径")
# 将 “要转码的视频文件夹路径” 修改为需要转码的文件夹路径即可
```
![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-11-12%20143310.png)

## 自定义转码数据保存路径
将 run_ff 方法中要修改的 x_value 预设值的 filter_data、transcoding_data 变量的值为自定义文件路径即可
```
filter_data = f"文件路径/筛选数据.json"
transcoding_data = "文件路径/转码数据.json"

# 将 “文件路径” 修改为自定义的文件夹路径即可
```
![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-11-12%20134543.png)

 ## 默认使用N卡编码加速
 如需A卡、CPU编码，请自行修改：

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

![image](.%2Fimg%2F%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202023-01-13%20012320.png)
