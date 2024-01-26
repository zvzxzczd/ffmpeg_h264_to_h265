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


def rw_no_type(yes, no, filter_data):
    """判断是否已存在该文件路径，如果存在则不写入到当前时间的对应键值中 """
    cache_yes_list = []
    yes_list = []  # 匹配数据
    cache_no_list = []
    no_list = []  # 未匹配
    ow_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    try:
        with open(filter_data, "r", encoding="utf-8") as jw:
            to_configure = json.load(jw)
    except:
        to_configure = {"支持的格式": {}, "不支持格式": {}}
        with open(filter_data, "w", encoding="utf-8") as jw:
            json.dump(to_configure, jw, indent=4, ensure_ascii=False)

    if "支持的格式" not in to_configure:
        to_configure["支持的格式"] = {}
    if "不支持格式" not in to_configure:
        to_configure["不支持格式"] = {}

    for k, v in to_configure["支持的格式"].items():
        cache_yes_list += v

    yes_set_cache_and = list(set(cache_yes_list) & set(yes))  # 取得要转码数据和支持数据的重叠数据的列表
    yes_list = list(set(yes) ^ set(yes_set_cache_and))  # 取得重叠数据和读取到的匹配数据的差异，输出为本次读取到的新数据
    """
    for i in yes:
        if i not in cache_yes_list:
            yes_list.append(i)"""

    for k, v in to_configure["不支持格式"].items():
        cache_no_list += v

    no_set_cache_and = list(set(cache_no_list) & set(no))  # 取得不匹配文件类型和支持数据的重叠数据的列表
    no_list = list(set(no) ^ set(no_set_cache_and))  # 取得重叠数据和读取到的不匹配文件类型的差异，输出为本次读取到的新数据
    """
    for i in no:
        if i not in cache_no_list:
            no_list.append(i)"""

    # 如果有新增， 写入数据
    if len(yes_list) > 0:
        to_configure["支持的格式"][ow_time] = yes_list
    if len(no_list) > 0:
        to_configure["不支持格式"][ow_time] = no_list

    if len(yes_list) or len(no_list) > 0:
        with open(filter_data, "w", encoding="utf-8") as jw:
            json.dump(to_configure, jw, indent=4, ensure_ascii=False)


def r_json(transcoding_data):
    """读取保存编码信息 如果没有文件则创建空文件"""
    try:
        with open(transcoding_data, "r", encoding="utf-8") as jw:
            to_configure = json.load(jw)
    except:
        to_configure = {}
        with open(transcoding_data, "w", encoding="utf-8") as jw:
            json.dump(to_configure, jw, indent=4, ensure_ascii=False)

    return to_configure


def create_folder_and_path(file_path):
    """检查某个路径下的文件是否存在，如果文件不存在，创建文件夹"""
    try:
        re.search(r"(\.)(?!.*\.).{1,9}$", file_path).group()
        dir_path, file_name = os.path.split(file_path)
    except:
        dir_path = file_path
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果文件不存在，创建文件夹
        os.makedirs(dir_path, exist_ok=True)
        # 新建文件
        with open(file_path, 'w') as f:
            pass
        print(f"新建文件完成：{file_path}")


def test_walk_os(all_dir, file_name):
    """
    通过读取传入的文件 inode 值，如果大于1，则输出同 inode 的所有文件，等于 1 只输出当前文件
    包含传入链接，如果删除所有文件，需要注意
    :param all_dir:  所有的文件路径
    :param file_name: 要处理的文件路径
    :return:
    """
    # 读取传入的文件 inode 值
    inode_number = os.stat(file_name).st_ino
    # 输出同 inode 值的所有文件的列表
    file_list = []
    # 遍历传入需要清除的硬链接文件根路径，并输出结果
    # 如果大于1，则输出同 inode 的所有文件
    if os.stat(file_name).st_nlink > 1:
        # 遍历传入根路径
        for path, _, files in os.walk(all_dir):
            for file in files:
                # 合成文件路径
                file_path = os.path.join(path, file).replace('\\', '/')
                # 如果是同一个 inode 值
                if os.stat(file_path).st_ino == inode_number:
                    # 添加路径到输出的列表中
                    if file_path not in file_list:  # 当前路径不在列表中，避免重复
                        file_list.append(file_path)
    # 等于 1 只输出当前文件路径列表
    if os.stat(file_name).st_nlink == 1:
        file_list.append(file_name)
    # 等于 0 空列表
    elif os.stat(file_name).st_nlink == 0:
        pass

    return file_list


class Ffm_run:
    """ 按设置参数转码文件"""

    def __init__(self, **kwargs):
        """
        :param read_directory 读取目录\n
        write_directory 写入目录\n
        coding_loss 缓存编码损失过大的文件夹\n
        type_v 变更后的文件类型\n
        filter_data 筛选数据保存的位置\n
        transcoding_data 转码文件保存的位置\n
        json_w 测试用，用于设置是否开启写入json选项，默认写入，不写入则需设置为 False\n
        """
        if "read_directory" not in kwargs:
            kwargs["read_directory"] = "./videos/缓存"
            create_folder_and_path(kwargs["read_directory"])  # 检测文件是否存在，不存在则新建路径及文件
        if "write_directory" not in kwargs:
            kwargs["write_directory"] = "./videos/输出"
            create_folder_and_path(kwargs["write_directory"])  # 检测文件是否存在，不存在则新建路径及文件
        if "coding_loss" not in kwargs:
            kwargs["coding_loss"] = "./videos/编码损失"
            create_folder_and_path(kwargs["coding_loss"])  # 检测文件是否存在，不存在则新建路径及文件
        if "type_v" not in kwargs:
            kwargs["type_v"] = [".mp4"]
        if "video_types" not in kwargs:
            kwargs["video_types"] = ['.mov', '.avi', '.m4v', '.mpg', '.ts', '.mkv', '.m2ts', '.mp4', ]
        if "filter_data" not in kwargs:
            kwargs["filter_data"] = r"./转码配置/筛选数据.json"
            create_folder_and_path(kwargs["filter_data"])  # 检测文件是否存在，不存在则新建路径及文件
        if "transcoding_data" not in kwargs:
            kwargs["transcoding_data"] = r"./转码配置/转码数据.json"
            create_folder_and_path(kwargs["transcoding_data"])  # 检测文件是否存在，不存在则新建路径及文件
        if "json_w" not in kwargs:  # 默认写入文件，测试环境设置False 则不写入
            kwargs["json_w"] = True

        self.read_directory = kwargs["read_directory"]  # 读取目录
        self.write_directory = kwargs["write_directory"]  # 写入目录
        self.coding_loss = kwargs["coding_loss"]  # 缓存编码损失过大的文件夹
        self.video_types = kwargs["video_types"]  # 要读取的文件类型
        self.type_v = kwargs["type_v"]  # 变更的文件类型 兼容性，只选择第一个值
        self.filter_data = kwargs["filter_data"]  # 筛选数据保存的位置
        self.transcoding_data = kwargs["transcoding_data"]  # 转码文件保存的位置
        self.json_w = kwargs["json_w"]  # 默认写入文件，测试环境设置False 则不写入
        self.remove_file_list = None  # 要删除的文件及对应的所有硬链接路径列表，用于避免多次转码，文件重复出现，使用时请在调用处或使用完成后初始化

        self.video_encoding = ['vp8', 'avc', 'realvideo 4', 'jpeg', 'mpeg video', 'mpeg-4 visual']  # 限定编码类型
        self.video_bit = 10000000  # 码率控制线

        
        # 读取到的列表
        self.catalog_file = []  # 所有文件及路径

        # json_data_dict【键】 =0 未处理 =1 已经转码  =2  转码失败 =3  不支持的编码 =4 损失过大 =5 读取编码信息错误 =6 文件过大
        read_cache = r_json(self.transcoding_data)  # 对已经转码的文件予以排除的字典初始化读取本地保存的文件
        self.json_data_dict = copy.deepcopy(read_cache)  # 深度复制
        self.cache_ff_run_dict = {}  # 本次运行转码结果的状态缓存，转码结束后显示本次运行的转码数据结果

        # 单文件
        self.path_file = ''  # 初始化读取文件夹
        self.out_file = ''  # 初始化 写入文件夹
        self.my_format = ''  # 文件 编码格式
        self.file = ''  # 临时保存文件名，带后缀
        self.encoding_bool = False  # 判断文件为限定编码中，不是则跳过
        self.bit_rate = 0  # 读取到的码率
        self.width = 0  # 视频宽
        self.height = 0  # 视频高
        self.ff = None  # 等待生成的转码命令

        self.f_print = '-' * 150  # 分隔符 打印格式化

    def re_name_file(self):
        """重命名文件"""
        old_name = os.path.basename(self.path_file)  # 取得文件名
        dir_name = os.path.dirname(self.path_file)  # 获得文件路径
        new_name = re.sub(r"_AVC_", r"_HEVC_", old_name)
        new_file_name = os.path.join(
            dir_name, new_name).replace('\\', '/')  # 合成新的路径
        return new_file_name

    def json_w_data(self):
        """决定是否写入本地文件"""
        if self.json_w:
            with open(self.transcoding_data, "w", encoding="utf-8") as jw:
                json.dump(self.json_data_dict, jw, indent=4, ensure_ascii=False)

    def js_dict(self):
        """生成关键字对应字典，并初始化键值 0 为未转码 1 为已转码 """
        # 赋予完成状态 0 未完成 1 完成 2 转码失败 3 不支持 4 损失过大 5 读取编码信息错误 6 文件过大

        try:
            # 跳过录屏 因为转码速度太慢
            cache_recording = re.search(r"Screenrecorder", self.path_file, flags=re.I).group()
            print(f"跳过： {self.path_file}")
        except AttributeError:
            cache_recording = ''

        if cache_recording == "Screenrecorder":  # 跳过录屏文件，因为转码速度太慢
            self.json_data_dict[self.path_file] = 3
            self.cache_ff_run_dict[self.path_file] = 3  # 写入本次运行转码结果的状态
            self.json_w_data()

        elif self.path_file not in self.json_data_dict:  # 避免对截屏文件产生两次比对和写入
            self.json_data_dict[self.path_file] = 0
            self.cache_ff_run_dict[self.path_file] = 0  # 写入本次运行转码结果的状态
            self.json_w_data()

    def width_height(self):
        """确定最低码率和适合的码率"""
        
        self.bit_rate = self.bit_rate // 1000  # 转换为 K
        # cache_bit = copy.deepcopy(self.bit_rate)  # 复制转换后的参数
        low = size_low(self.width, self.height)
        if low <= 480:  # 480P及以下
            if self.bit_rate <= 900:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 900:
                self.bit_rate = int(self.bit_rate * 0.3)
                if self.bit_rate <= 700:
                    self.bit_rate = 700
                return "B"

        elif 480 < low <= 720:  # 480P以上720P及以下
            if self.bit_rate <= 1200:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 1200:
                self.bit_rate = int(self.bit_rate * 0.4)
                if self.bit_rate <= 1000:
                    self.bit_rate = 1000
                return "B"

        elif 720 < low <= 960:  # 720P以上960P及以下
            if self.bit_rate <= 2000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 2000:
                self.bit_rate = int(self.bit_rate * 0.4)
                if self.bit_rate <= 1700:
                    self.bit_rate = 1700
                return "B"

        elif 960 < low <= 1080:  # 960P以上1080P及以下
            if self.bit_rate <= 3000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 3000:
                self.bit_rate = int(self.bit_rate * 0.5)
                if self.bit_rate <= 2500:
                    self.bit_rate = 2500
                return "B"

        elif 1080 < low <= 1440:  # 1080P以上1440P及以下
            if self.bit_rate <= 4800:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 4800:
                self.bit_rate = int(self.bit_rate * 0.5)
                if self.bit_rate <= 4000:
                    self.bit_rate = 4000
                return "B"

        elif 1440 < low <= 1600:  # 1440P以上1600P及以下
            if self.bit_rate <= 6000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 6000:
                self.bit_rate = int(self.bit_rate * 0.5)
                if self.bit_rate <= 5000:
                    self.bit_rate = 5000
                return "B"

        elif 1600 < low <= 2160:  # 1600P以上2160P及以下
            if self.bit_rate <= 8000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 8000:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 6500:
                    self.bit_rate = 6500
                return "B"

        elif low > 2160:  # 2160P以上
            if self.bit_rate <= 12000:
                return "A"  # self.bit_rate = cache_bit
            if self.bit_rate > 12000:
                self.bit_rate = int(self.bit_rate * 0.6)
                if self.bit_rate <= 10000:
                    self.bit_rate = 10000
                return "B"
        # print(self.bit_rate)

    def get_video_info(self):
        """判断文件编码类型"""
        try:
            mi = MediaInfo.parse(self.path_file)
            self.my_format = mi.to_data(
            )['tracks'][1]['format'].lower()  # 读取编码，并小写方便比对
            self.bit_rate = mi.to_data()['tracks'][1]['bit_rate']  # 码率
            self.width = mi.to_data()['tracks'][1]['width']  # 视频宽
            self.height = mi.to_data()['tracks'][1]['height']  # 视频高
            # print('MediaInfo 编码： {:<15}源视频路径: {}'.format(self.my_format, self.path_file, ))
        except:
            self.json_data_dict[self.path_file] = 5  # 写入状态，读取文件信息失败
            self.cache_ff_run_dict[self.path_file] = 5  # 写入本次运行转码结果的状态
            self.json_w_data()
            self.encoding_bool = False

        if self.json_data_dict[self.path_file] != 5:
            if self.my_format in self.video_encoding:
                self.encoding_bool = True
            else:
                self.encoding_bool = False

                print('编码：{:<15}非预定编码， 源视频路径: {}'.format(
                    self.my_format, self.path_file, ))

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
        """转码命令合成及运行"""

        ca_bit = self.width_height()  # 码率决策

        if ca_bit == "A":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -crf 18'})
        elif ca_bit == "B":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -b:v {self.bit_rate}K'})

        print(self.ff.cmd)
        self.ff.run()  # 可以注释该行测试是否能够正确的分段时间

    def ffmpeg_run_nocopy(self):
        """转码命令合成及运行"""

        ca_bit = self.width_height()  # 码率决策

        if ca_bit == "A":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -crf 18'})
        elif ca_bit == "B":  # 码率控制策略
            self.ff = FFmpeg(inputs={f'{self.path_file}': "-hwaccel auto"},
                             outputs={f'{self.out_file}': f'-c:v hevc_nvenc -b:v {self.bit_rate}K'})

        print(self.ff.cmd)
        self.ff.run()  # 可以注释该行测试是否能够正确的分段时间

    def n_link_flie(self):
        """删除文件后，检测有没有硬链接，删除所有旧硬链接，并重新创建新的对应的硬链接。
        如果文件存在，则重命名转码文件后移动，管理源文件的硬链接并重新创建新的硬链接"""
        self.remove_file_list = None  # 初始化
        if os.path.exists(self.path_file):  # 判断源文件是否存在,如果文件被删除，会出现同inode的文件未被删除完成，再次转码该inode文件，
            # os.remove(self.path_file)  # 如果存在则删除源文件，已更新到读取所有硬链接后删除 此行已失效
            # 读取当前硬链接的文件
            self.remove_file_list = test_walk_os(self.read_directory, self.path_file)
            # 遍历列表并逐个删除
            n_remove = 0
            print(f"\n删除当前转码 inode 号： {os.stat(self.path_file).st_ino} 共 "
                  f"{os.stat(self.path_file).st_nlink} 个连接数所指向的文件路径：")
            for one_file_name in self.remove_file_list:
                os.remove(one_file_name)
                n_remove += 1
                print(f"已删除 第 {n_remove} 个文件路径 >>>>> {one_file_name}")
            print('-' * 50)

        # 移动文件后建立硬链接
        cache_dir = os.path.dirname(self.path_file)  # 去掉文件名，单独返回目录路径
        if not os.path.exists(cache_dir):  # 路径不存在，则递归创建 避免文件夹删除的情况
            # 传入一个path路径，生成一个递归的文件夹；如果文件夹存在，就会报错,因此创建文件夹之前，需要使用os.path.exists(path)函数判断文件夹是否存在；
            os.makedirs(cache_dir, exist_ok=True)  # makedirs 创建文件时如果路径不存在会创建这个路径
        try:  # 20240125 更新str()
            print(f"移动文件: {self.out_file} >>>>>> {cache_dir}")
            shutil.move(str(self.out_file), str(cache_dir))  # 移动文件
        except shutil.Error as err:  # 移动失败后处理
            # 避免多次转码出现长串文件名问题 20240125 更新str()
            self.out_file = re.sub(r"(_?转码文件名重复)+\.mp4$", '.mp4',
                                   str(self.out_file), flags=re.I)
            # 正则添加重复文件的名称
            self.out_file = re.sub("\\.mp4$", '_转码文件名重复.mp4',
                                   self.out_file, flags=re.I)
            shutil.move(self.out_file, cache_dir)  # 移动文件
            print(err)  # 打印错误信息
            # 将 self.remove_file_list 列表内的变量也重命名
            cache_list = []  # 初始化
            for err_name in self.remove_file_list:
                err_name = re.sub("\\.mp4$", '_转码文件名重复.mp4',
                                  str(err_name), flags=re.I)
                cache_list.append(err_name)
            self.remove_file_list = copy.deepcopy(cache_list)  # 更新列表内容

        # 当源文件删除后，没有读取到硬链接路径列表后，已经移动转码文件的情况的情况
        if self.remove_file_list is not None:
            # 拆分获得路径、文件名
            ___path, ___name = os.path.split(self.out_file)
            # 组装转码和移动完成后的路径+文件名
            new_file_dir_ = os.path.join(cache_dir, ___name).replace("\\", "/")
            if len(self.remove_file_list) > 1:
                for file_nlink in self.remove_file_list:
                    # 去除文件后缀 合成转码移动后的文件路径
                    cache__path, __ = os.path.splitext(file_nlink)
                    file_dir_all = f"{cache__path}.mp4"  # 要创建硬链接的 路径+文件名+后缀
                    if not os.path.exists(file_dir_all):  # 如果文件不存在
                        try:
                            print(f"创建硬链接: {new_file_dir_} >> {file_dir_all}")
                            os.link(new_file_dir_, file_dir_all)  # 创建硬链接
                            # print("创建硬链接完成。")
                        except:
                            print(f'\n创建硬链接失败，请检查文件：{new_file_dir_} >> {file_dir_all}\n')
                    else:  # 如果文件存在
                        # 如果文件存在，且不是转码完成移动后的文件或者同一个 inode 号的文件，重命名后闯将硬链接
                        if os.stat(file_dir_all).st_ino != os.stat(new_file_dir_).st_ino:
                            # 重命名文件，且避免多次转码出现长串文件名问题
                            file_dir_all = re.sub(r"(_?硬链接文件名重复)+\.mp4$", '.mp4',
                                                  str(file_dir_all), flags=re.I)
                            file_dir_all = re.sub("\\.mp4$", '_硬链接文件名重复.mp4',
                                                  file_dir_all, flags=re.I)
                            if os.path.exists(file_dir_all):  # 删除重命名文件后，仍然存在，则删除目标文件夹内的冲突文件
                                os.remove(file_dir_all)
                            try:
                                print(f"文件名称重复，重命名后创建硬链接: {new_file_dir_} >> {file_dir_all}")
                                os.link(new_file_dir_, file_dir_all)  # 创建硬链接
                                # print("创建硬链接完成。")
                            except:
                                print(
                                    f'\n文件名称重复，重命名后创建硬链接失败，请检查文件：{new_file_dir_} >> {file_dir_all}\n')

    def transcoding(self):
        """运行"""
        # 读取文件
        self.catalog_file, no_file = Compares(read_output=self.read_directory, write_enter=self.write_directory,
                                              ph_types=self.video_types, w_types=self.type_v, w_json_bool=False,
                                              new_makedirs=False).direct_results()
        if self.json_w:  # 写入未匹配到的数据
            rw_no_type(self.catalog_file, no_file, self.filter_data)
            # print(1564566547899678)
            # time.sleep(10)

        for self.path_file in self.catalog_file:
            # print(1564566547899678)
            # time.sleep(2)

            self.js_dict()  # 确定文件是否新增转码文件，如果不存在，则赋值
            # self.json_w_data()  # 写入在 self.js_dict() 中执行

            fll_name, file_extension = os.path.splitext(str(self.path_file))
            # 写入根目录 # 修改此两行 决定写入 子文件夹还是根目录
            self.file = os.path.basename(fll_name + self.type_v[0])  # 变更后缀，并获得文件名
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

                        try:
                            os.remove(self.out_file)  # 删除转码失败的文件
                        except FileNotFoundError:
                            pass

                        try:
                            self.bit_rate = cache_bit  # 将码率信息恢复到处理前的状态
                            self.ffmpeg_run_nocopy()
                        except:
                            print(f"第二次转码尝试失败:{self.path_file}\n{self.f_print}")
                            # 写入状态，转码失败
                            # self.json_data_dict[self.path_file] = 2
                            # self.cache_ff_run_dict[self.path_file] = 2  # 写入本次运行转码结果的状态
                            # self.json_w_data()
                            # continue  # 再次转码失败，跳过该文件。

                    # 读取转码后，转码前文件大小
                    old = os.stat(self.path_file).st_size
                    try:  # 如果前面两次转码失败，跳过该文件处理
                        new = os.stat(self.out_file).st_size

                        if new > 1024:

                            if old // new > 8:
                                # 写入状态，转码损失过大
                                self.json_data_dict[self.path_file] = 4
                                self.cache_ff_run_dict[self.path_file] = 4  # 写入本次运行转码结果的状态
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
                                    print(f"移动文件失败：{self.out_file}\n删除转码文件！\n{self.f_print}")
                                    sys.exit()

                            if old // new <= 8:
                                # 移动文件
                                if new >= old:  # 转码文件大于等于源文件
                                    os.remove(self.out_file)  # 删除转码失败的文件
                                    # 写入状态，转码文件过大
                                    self.json_data_dict[self.path_file] = 6
                                    self.cache_ff_run_dict[self.path_file] = 6  # 写入本次运行转码结果的状态
                                    self.json_w_data()
                                else:
                                    # 删除源文件，移动文件并重新链接文件
                                    self.n_link_flie()
                                    print(f"转码成功:{self.path_file}\n{self.f_print}")

                                    # 写入状态，转码完成
                                    self.json_data_dict[self.path_file] = 1
                                    self.cache_ff_run_dict[self.path_file] = 1  # 写入本次运行转码结果的状态
                                    self.json_w_data()

                        elif new <= 1024:
                            os.remove(self.out_file)  # 删除转码失败的文件
                            self.json_data_dict[self.path_file] = 2  # 写入状态，转码失败
                            self.cache_ff_run_dict[self.path_file] = 2  # 写入本次运行转码结果的状态
                            self.json_w_data()

                    except FileNotFoundError:  # 转码文件两次都失败后，如果不存在该文件的处理方法
                        try:
                            os.remove(self.out_file)  # 删除转码失败的文件
                            self.json_data_dict[self.path_file] = 2  # 写入状态，转码失败
                            self.cache_ff_run_dict[self.path_file] = 2  # 写入本次运行转码结果的状态
                            self.json_w_data()
                        except:
                            self.json_data_dict[self.path_file] = 2  # 写入状态，转码失败
                            self.cache_ff_run_dict[self.path_file] = 2  # 写入本次运行转码结果的状态
                            self.json_w_data()

                else:
                    # 将不是预定编码的文件路径及文件名写入JSON之类的字典文件中。
                    self.json_data_dict[self.path_file] = 3  # 写入状态，不支持该类型的编码视频
                    self.cache_ff_run_dict[self.path_file] = 3  # 写入本次运行转码结果的状态
                    self.json_w_data()

            elif self.json_data_dict[self.path_file] == 1:
                # print("""该文件已完成转码！""")
                continue  # 如果已经转码，跳过

        # for k, v in self.json_data_dict.items():  # 历史所有的转码数据结果输出
        for k, v in self.cache_ff_run_dict.items():  # 本次运行的转码数据结果输出
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


def run_ff(x_value=None, write_folder=None, write_loss=None, y_dist=None, json_w=True):
    """
    运行转码
    :param x_value: 1：默认 ./视频 文件夹  2：默认 ./下载文件夹 ，可以传入自定义参数
    :param write_folder: 视频缓存文件夹
    :param write_loss: 码率损失过大的保存文件夹，转码后不会删除源文件
    :param y_dist: x_value下已设置默认需转码的路径，可以自定义传入 y_dist=需要转码的路径，也可以不设置x_value,直接传入y_dist=需要转码的路径
    :param json_w: 默认True,  写入 JSON 数据， 传入False则不写入数据
    """

    sss = time.time()

    types = ['.mov', '.avi', '.m4v', '.mpg', '.ts', '.mkv', '.m2ts', '.mp4', ]
    w_fil_types = [".mp4"]
    if write_folder is None:
        write_folder = "./转码缓存/输出"  # 转码中文件临时写入路径
    if not os.path.exists(write_folder):  # 如果文件不存在，创建文件夹
        os.makedirs(write_folder, exist_ok=True)
    if write_loss is None:
        write_loss = "./转码缓存/编码损失"  # 损失过大保存路径
    if not os.path.exists(write_loss):  # 如果文件不存在，创建文件夹
        os.makedirs(write_loss, exist_ok=True)

    if x_value == 1:  # 运行 视频 文件夹文件转码，写入json数据
        if y_dist is None:
            read_folder = "./视频"  # 读取
        else:
            read_folder = y_dist


        filter_data = f"{read_folder}/json_data/筛选数据.json"
        create_folder_and_path(filter_data)  # 检测文件是否存在，不存在则新建路径及文件
        transcoding_data = f"{read_folder}/json_data/转码数据.json"
        create_folder_and_path(transcoding_data)  # 检测文件是否存在，不存在则新建路径及文件

        ff_r = Ffm_run(read_directory=read_folder, write_directory=write_folder, coding_loss=write_loss,
                       video_types=types, filter_data=filter_data, transcoding_data=transcoding_data,
                       type_v=w_fil_types, )  # 未设置 json_w=False 写入json数据
        ff_r.transcoding()

    elif x_value == 2:  # 运行 下载文件夹 下转码，不写入json数据
        if y_dist is None:
            read_folder = r"./下载文件夹"  # 该文件夹 需复制配置/新建文件夹/图片文件夹 记录使用
        else:
            read_folder = y_dist
        filter_data = f"{read_folder}/json_data/筛选数据.json"
        create_folder_and_path(filter_data)  # 检测文件是否存在，不存在则新建路径及文件
        transcoding_data = f"{read_folder}/json_data/转码数据.json"
        create_folder_and_path(transcoding_data)  # 检测文件是否存在，不存在则新建路径及文件

        ff_r = Ffm_run(read_directory=read_folder, write_directory=write_folder, coding_loss=write_loss,
                       video_types=types, filter_data=filter_data, transcoding_data=transcoding_data,
                       type_v=w_fil_types, json_w=json_w)  # 根据传入json_w参数确定是否写入json数据
        ff_r.transcoding()

    else:
        if y_dist is None:
            read_folder = str(input("文件路径为空，请重新输入要转码的文件路径: "))  # 读取
            read_folder = re.sub(r"\n|\t|\s|^\"|\"$", r"", read_folder).replace("\\", "/")  # 去除空格 换行 制表符 及标点符号
        else:
            read_folder = y_dist
            read_folder = re.sub(r"\n|\t|\s|^\"|\"$|\\$|/$", r"", read_folder).replace("\\", "/")  # 去除末尾斜杠或反斜杠

        filter_data = f"{read_folder}/json_data/筛选数据.json"
        create_folder_and_path(filter_data)  # 检测文件是否存在，不存在则新建路径及文件
        transcoding_data = f"{read_folder}/json_data/转码数据.json"
        create_folder_and_path(transcoding_data)  # 检测文件是否存在，不存在则新建路径及文件

        ff_r = Ffm_run(read_directory=read_folder, write_directory=write_folder, coding_loss=write_loss,
                       video_types=types, filter_data=filter_data, transcoding_data=transcoding_data,
                       type_v=w_fil_types, json_w=json_w)  # 根据传入json_w参数确定是否写入json数据
        ff_r.transcoding()

    print(time.time() - sss)


if __name__ == "__main__":
    test_dir = r"C:/测试/风景"  # 传入路径

    # 以预设参数运行
    # run_ff(1)

    # 传入文件夹参数，不写入json数据
    run_ff(y_dist=test_dir, json_w=False)
