import copy
import json
import os
import re
import shutil
import sys
import time

from ffmpy3 import FFmpeg
from pymediainfo import MediaInfo

from 读取差异文件 import Compares


def size_low(aaaaaa, bbbbbb):
    """确定最短边"""
    if aaaaaa > bbbbbb:
        return bbbbbb
    elif aaaaaa <= bbbbbb:
        return aaaaaa


def r_json():
    # 读取保存编码信息 如果没有文件则创建空文件
    try:
        with open("D:/Program_Files/转码配置/转码数据.json", "r", encoding="utf-8") as jw:
            to_configure = json.load(jw)
    except:
        to_configure = {}
        with open("D:/Program_Files/转码配置/转码数据.json", "w", encoding="utf-8") as jw:
            json.dump(to_configure, jw, indent=4, ensure_ascii=False)

    return to_configure


def rw_no_type(yes, no):
    """判断是否已存在该文件路径，如果存在则不写入到当前时间的对应键值中 """
    cache_yes_list = []
    yes_list = []  # 匹配数据
    cache_no_list = []
    no_list = []  # 未匹配
    ow_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    try:
        with open("D:/Program_Files/转码配置/筛选数据.json", "r", encoding="utf-8") as jw:
            to_configure = json.load(jw)
    except:
        to_configure = {"支持的格式": {}, "不支持格式": {}}
        with open("D:/Program_Files/转码配置/筛选数据.json", "w", encoding="utf-8") as jw:
            json.dump(to_configure, jw, indent=4, ensure_ascii=False)

    if "支持的格式" not in to_configure:
        to_configure["支持的格式"] = {}
    if "不支持格式" not in to_configure:
        to_configure["不支持格式"] = {}

    for k, v in to_configure["支持的格式"].items():
        cache_yes_list += v
    for i in yes:
        if i not in cache_yes_list:
            yes_list.append(i)

    for k, v in to_configure["不支持格式"].items():
        cache_no_list += v
    for i in no:
        if i not in cache_no_list:
            no_list.append(i)

    # 如果有新增， 写入数据
    if len(yes_list) > 0:
        to_configure["支持的格式"][ow_time] = yes_list
    if len(no_list) > 0:
        to_configure["不支持格式"][ow_time] = no_list

    if len(yes_list) or len(no_list) > 0:
        with open("D:/Program_Files/转码配置/筛选数据.json", "w", encoding="utf-8") as jw:
            json.dump(to_configure, jw, indent=4, ensure_ascii=False)


class Ffm_run:
    """
    运行转码
    read_directory 读取目录
    write_directory 写入目录
    coding_loss 缓存编码损失过大的文件夹
    type_v:变更的文件类型
    json_w:测试用，用于设置是否开启写入json选项
    """

    def __init__(self, **kwargs):
        """
        read_directory 读取目录
        write_directory 写入目录
        coding_loss 缓存编码损失过大的文件夹
        type_v:变更的文件类型
        json_w:测试用，用于设置是否开启写入json选项
        """
        if "read_directory" not in kwargs:
            kwargs["read_directory"] = "D:/Program_Files/Cache/cache/videos/缓存"
        if "write_directory" not in kwargs:
            kwargs["write_directory"] = "D:/Program_Files/Cache/cache/videos/输出"
        if "coding_loss" not in kwargs:
            kwargs["coding_loss"] = "D:/Program_Files/Cache/cache/videos/编码损失"
        if "type_v" not in kwargs:
            kwargs["type_v"] = [".mp4"]
        if "video_types" not in kwargs:
            kwargs["video_types"] = ['.mov', '.avi', '.m4v',
                                     '.mpg', '.ts', '.mkv', '.m2ts', '.mp4', ]
        if "json_w" not in kwargs:  # 默认写入文件，测试环境设置False 则不写入
            kwargs["json_w"] = True

        self.read_directory = kwargs["read_directory"]  # 读取目录
        self.write_directory = kwargs["write_directory"]  # 写入目录
        self.coding_loss = kwargs["coding_loss"]  # 缓存编码损失过大的文件夹
        self.video_types = kwargs["video_types"]  # 要读取的文件类型
        self.type_v = kwargs["type_v"]  # 变更的文件类型 兼容性，只选择第一个值
        self.video_encoding = ['vp8', 'avc', 'realvideo 4',
                               'jpeg', 'mpeg video', 'mpeg-4 visual']  # 限定编码类型
        self.json_w = kwargs["json_w"]  # 默认写入文件，测试环境设置False 则不写入
        self.video_bit = 10000000  # 码率控制线

        # 读取到的列表
        self.catalog_file = []  # 所有文件及路径

        #   json_data_dict【键】 =0 未处理 =1 已经转码  =2  转码失败 =3  不支持的编码 =4 损失过大 =5 读取编码信息错误 =6 文件过大
        self.json_data_dict = r_json()  # 对已经转码的文件予以排除的字典初始化读取本地保存的文件

        # 单文件
        self.path_file = ''  # 初始化读取文件夹
        self.out_file = ''  # 初始化 写入文件夹
        self.my_format = ''  # 文件 编码格式
        self.file = ''  # 临时保存文件名，带后缀
        self.encoding_bool = False  # 判断文件为限定编码中，不是则跳过
        self.bit_rate = 0  # 读取到的码率
        self.width = 0  # 视频宽
        self.height = 0  # 视频高
        self.ff = None

    def re_name_file(self):
        """重命名文件"""
        old_name = os.path.basename(self.path_file)  # 取得文件名
        dir_name = os.path.dirname(self.path_file)  # 获得文件路径
        new_name = re.sub(r"_AVC_", r"_HEVC_", old_name)
        new_file_name = os.path.join(dir_name, new_name).replace('\\', '/')  # 合成新的路径
        return new_file_name

    def json_w_data(self):
        """决定是否写入本地文件"""
        if self.json_w:
            with open("D:/Program_Files/转码配置/转码数据.json", "w", encoding="utf-8") as jw:
                json.dump(self.json_data_dict, jw,
                          indent=4, ensure_ascii=False)

    def js_dict(self):
        """生成关键字对应字典，并初始化键值 0 为未转码 1 为已转码 """
        if self.path_file not in self.json_data_dict:
            # 赋予完成状态 0 未完成 1 完成 2 转码失败 3 不支持 4 损失过大 5 读取编码信息错误 6 文件过大
            self.json_data_dict[self.path_file] = 0

    def width_height(self):
        """确定最低码率和适合的码率"""

        self.bit_rate = self.bit_rate // 1000  # 转换为 K
        # cache_bit = copy.deepcopy(self.bit_rate)  # 复制转换后的参数
        low = size_low(self.width, self.height)
        if low <= 480:  # 480P及以下
            if self.bit_rate <= 900:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 900:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 700:
                    self.bit_rate = 700
                return "B"

        if 480 < low <= 720:  # 480P以上720P及以下
            if self.bit_rate <= 1800:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 1800:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 1500:
                    self.bit_rate = 1500
                return "B"

        if 720 < low <= 960:  # 720P以上960P及以下
            if self.bit_rate <= 2000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 2000:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 1700:
                    self.bit_rate = 1700
                return "B"

        if 960 < low <= 1080:  # 960P以上1080P及以下
            if self.bit_rate <= 3000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 3000:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 2500:
                    self.bit_rate = 2500
                return "B"

        if 1080 < low <= 1440:  # 1080P以上1440P及以下
            if self.bit_rate <= 4800:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 4800:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 4000:
                    self.bit_rate = 4000
                return "B"

        if 1440 < low <= 1600:  # 1440P以上1600P及以下
            if self.bit_rate <= 6000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 6000:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 5000:
                    self.bit_rate = 5000
                return "B"

        if 1600 < low <= 2160:  # 1600P以上2160P及以下
            if self.bit_rate <= 8000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 8000:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 6500:
                    self.bit_rate = 6500
                return "B"
        # print(self.bit_rate)

    def get_video_info(self):
        """判断文件编码类型"""
        try:
            mi = MediaInfo.parse(self.path_file)
            self.my_format = mi.to_data()['tracks'][1]['format'].lower()  # 读取编码，并小写方便比对
            self.bit_rate = mi.to_data()['tracks'][1]['bit_rate']  # 码率
            self.width = mi.to_data()['tracks'][1]['width']  # 视频宽
            self.height = mi.to_data()['tracks'][1]['height']  # 视频高
            # print('MediaInfo 编码： {:<15}源视频路径: {}'.format(self.my_format, self.path_file, ))
        except:
            self.json_data_dict[self.path_file] = 5  # 写入状态，读取文件信息失败
            self.json_w_data()
            self.encoding_bool = False

        if self.my_format in self.video_encoding:
            self.encoding_bool = True
        else:
            self.encoding_bool = False

            print('编码：{:<15}非预定编码， 源视频路径: {}'.format(
                self.my_format, self.path_file, ))
            pass

    def ffmpeg_run(self):
        """开始转码"""

        ca_bit = self.width_height()  # 码率决策

        if ca_bit == "A":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -crf 18 -c:a copy'})
        elif ca_bit == "B":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -b:v {self.bit_rate}K -c:a copy'})

        print(self.ff.cmd)
        self.ff.run()  # 可以注释该行测试是否能够正确的分段时间

    def ffmpeg_run_nocopy(self):
        """开始转码"""

        ca_bit = self.width_height()  # 码率决策

        if ca_bit == "A":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -crf 18'})
        elif ca_bit == "B":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -b:v {self.bit_rate}K'})

        print(self.ff.cmd)
        self.ff.run()  # 可以注释该行测试是否能够正确的分段时间

    def transcoding(self):
        """运行"""
        # 读取文件
        self.catalog_file, no_file = Compares(read_output=self.read_directory, write_enter=self.write_directory,
                                              ph_types=self.video_types, w_types=self.type_v, w_json_bool=False,
                                              new_makedirs=False).direct_results()
        if self.json_w:  # 写入未匹配到的数据
            rw_no_type(self.catalog_file, no_file)

        for self.path_file in self.catalog_file:

            self.js_dict()  # 确定文件是否新增转码文件，如果不存在，则赋值
            self.json_w_data()

            fll_name, file_extension = os.path.splitext(str(self.path_file))
            # 写入根目录 # 修改此两行 决写入 子文件夹还是根目录
            self.file = os.path.basename(
                fll_name + self.type_v[0])  # 变更后缀，并获得文件名
            self.out_file = os.path.join(
                self.write_directory, self.file).replace('\\', '/')  # 直接写入根目录缓存

            # print(f"\n\n{self.path_file}\n{self.out_file}")
            if self.json_data_dict[self.path_file] == 0:  # 判断是否处理过

                # 判断文件编码类型
                self.get_video_info()
                cache_bit = copy.deepcopy(self.bit_rate)  # 复制转换后的码率参数

                # 判断是否为预定编码,如果是，开始转码
                if self.encoding_bool:
                    if os.path.exists(self.out_file):
                        print(f"即将转码，删除已存在的文件： {self.out_file}")
                        os.remove(self.out_file)

                    try:  # 不支持copy 参数的 换方式运行

                        self.ffmpeg_run()
                    except:
                        print(f"第一次转码尝试失败:{self.path_file}")
                        os.remove(self.out_file)  # 删除转码失败的文件
                        try:
                            self.bit_rate = cache_bit  # 将码率信息恢复到处理前的状态
                            self.ffmpeg_run_nocopy()
                        except:
                            print(f"第二次转码尝试失败:{self.path_file}")
                            # 写入状态，转码失败
                            self.json_data_dict[self.path_file] = 2
                            self.json_w_data()
                            continue  # 再次转码失败，跳过该文件。

                    # 读取转码后，转码前文件大小
                    new, old = os.stat(self.out_file).st_size, os.stat(
                        self.path_file).st_size

                    if new > 1024:

                        if old // new > 8:
                            # 写入状态，转码损失过大
                            self.json_data_dict[self.path_file] = 4
                            self.json_w_data()
                            # 合成缓存文件路径，用于删除
                            cc_name = os.path.join(
                                self.coding_loss, self.file).replace('\\', '/')
                            if os.path.exists(cc_name):  # 如果文件存在，删除
                                os.remove(cc_name)
                            try:
                                shutil.move(self.out_file,
                                            self.coding_loss)  # 移动文件
                            except:
                                print(f"移动文件失败：{self.out_file}\n退出转码！")
                                sys.exit()

                        if old // new <= 8:
                            # 移动文件
                            if new >= old:  # 转码文件大于等于源文件
                                os.remove(self.out_file)  # 删除转码失败的文件
                                # 写入状态，转码文件过大
                                self.json_data_dict[self.path_file] = 6
                                self.json_w_data()
                            else:
                                if os.path.exists(self.path_file):  # 判断源文件是否存在
                                    os.remove(self.path_file)  # 如果存在则删除源文件

                                cache_dir = os.path.dirname(self.path_file)  # 获得文件路径
                                shutil.move(self.out_file, cache_dir)  # 移动文件
                                # 仅用于重命名舞蹈文件夹
                                # new_name = self.re_name_file()  # 获取新的文件名
                                # os.rename(self.path_file, new_name)

                                print(f"转码成功:{self.path_file}")

                                # 写入状态，转码完成
                                self.json_data_dict[self.path_file] = 1
                                self.json_w_data()

                    else:
                        os.remove(self.out_file)  # 删除转码失败的文件
                        self.json_data_dict[self.path_file] = 2  # 写入状态，转码失败
                        self.json_w_data()

                else:
                    # 将不是预定编码的文件路径及文件名写入JSON之类的字典文件中。
                    self.json_data_dict[self.path_file] = 3  # 写入状态，不支持该类型的编码视频
                    self.json_w_data()

            elif self.json_data_dict[self.path_file] == 1:
                print("""该文件已完成转码！""")
                continue  # 如果已经转码，跳过

        for k, v in self.json_data_dict.items():
            if v == 0:
                print(f"未转码: {k}")
            if v == 1:
                print(f"已完成: {k}")
            if v == 2:
                print(f"失  败: {k}")
            if v == 3:
                print(f"不支持: {k}")
            if v == 4:
                print(f"损失大: {k}")
            if v == 5:
                print(f"无信息: {k}")
            if v == 6:
                print(f"过  大: {k}")


if __name__ == "__main__":
    types = ['.mov', '.avi', '.m4v', '.mpg', '.ts', '.mkv', '.m2ts', '.mp4', ]
    w_fil_types = [".mp4"]
    read = "D:/Program_Files/Cache/cache/videos/缓存"  # 读取
    write = "D:/Program_Files/Cache/cache/videos/输出"  # 写缓存入
    loss = "D:/Program_Files/Cache/cache/videos/编码损失"  # 损失过大


    sss = time.time()
    #  非舞蹈文件夹需注释掉369行 370行的重命名
    ff_r = Ffm_run(read_directory=read, write_directory=write, coding_loss=loss,
                   video_types=types, type_v=w_fil_types,)  # json_w=False
    ff_r.transcoding()
    # a = repeat_inspection(file_list) 检查重复文件 需要调用检查重复文件.py的调用 字典比对效果更好

    print(time.time() - sss)
