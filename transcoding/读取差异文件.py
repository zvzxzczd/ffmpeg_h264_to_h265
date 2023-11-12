import json
import os
import re
import shutil
import time


class Wr_data:
    """硬盘写入新数据或者读取旧的数据"""

    def __init__(self, file_name, test_dir=None):
        if test_dir is None:
            test_dir = []
        self.file_name = file_name  # 存入的文件路径的文件名称
        self.test_dir = test_dir  # 要保存的的文件路径列表
        self.load_file = []  # 读取到的文件或者子文件夹的路径列表
        self.file_route = ''  # 备份的路径
        self.cache_name = ''  # 移动后，暂未更名的文件
        self.output = ''  # 备份文件路径加文件名称

    def refile_name(self):
        """组合成备份的文件名称"""
        cache_dir, name = os.path.dirname(self.file_name), os.path.basename(self.file_name)  # 获得路径及文件名称
        self.file_route = cache_dir + r"/备份数据"
        self.cache_name = self.file_route + r"/" + name  # 移动后文件的未更名的名称
        file_name, file_extension = os.path.splitext(str(self.cache_name))
        self.output = file_name + '_bak' + file_extension  # 移动后的文件需要变更为新的文件名

    def rename(self):
        """如果文件存在，删除后覆盖"""
        self.refile_name()
        if os.path.exists(self.file_name):
            # 检查文件啊是否已存在的简写，全文为 if os.path.existsz(self.filename) ==Ture
            # 如果存在原始文件，则备份文件
            if os.path.exists(self.output):
                try:
                    os.remove(self.output)
                except:
                    print("删除文件时出错！可能设置保存备份文件的：数据文件夹 名称错误！ 请检查名称！！！")
            try:
                # print(f"{self.file_name}\n{self.file_route}\n{self.cache_name}\n{self.output}\n\n")
                shutil.move(self.file_name, self.file_route)
                os.rename(self.cache_name, self.output)
                print("已创建备份文件：" + self.output)
            except WindowsError:
                print("创建备份文件失败！ 失败文件：" + self.output)
        elif not os.path.exists(self.file_name):
            print("待创建>>>>>>：" + self.file_name)

    def save_paths(self):
        """写入json数据"""
        self.rename()  # 检查文件是否存在，存在先行备份再写入
        # paths.sort()
        with open(self.file_name, 'w+', encoding='utf-8') as fd:  # encoding='utf-8' 指定编码格式
            json.dump(self.test_dir, fd, indent=4, ensure_ascii=False)
        print("已创建>>>>>>：" + self.file_name)

    def read_paths(self):
        """读取原始json"""
        self.refile_name()
        if os.path.exists(self.output):  # 判断文件是否存在
            with open(self.output, 'r', encoding='utf-8') as fl:  # encoding='utf-8' 指定编码格式
                try:
                    self.load_file = json.load(fl)
                except TypeError:
                    print('JSON 文件 为空')

    def return_load_file(self):
        """输出备份的json数据，如果为空，表示暂无备份数据"""
        self.read_paths()
        return self.load_file


class Files_read:
    """读取并输出子文件夹、所有文件的路径、不匹配的文件"""

    def __init__(self, read_output, ph_types):
        self.read_output = read_output  # 需要读取的路径
        self.ph_types = ph_types  # 初始化文件类型
        self.sub_folder = []  # 读取的子文件夹名称
        self.test_dir = []  # 读取的文件路径列表
        self.no_types = []  # 未能匹配到到的文件

    def all_files(self):  # 读取该路径下的具体路径+文件名称
        """读取该路径下的具体路径+文件名称"""
        for path, _, files in os.walk(self.read_output):
            pat = path.replace('\\', '/')
            self.sub_folder.append(pat)  # 保存子文件夹名称
            for file in files:
                # la = re.findall(r"\.\w{3,4}$", ll) 另一种实现的方式
                fll_name, file_extension = os.path.splitext(str(file))
                file_extension = file_extension.lower()  # 最小化名称，方便处理
                if file_extension in self.ph_types:  # 确定是为需要的文件类型并保存
                    self.test_dir.append(os.path.join(path, file).replace('\\', '/'))
                else:
                    self.no_types.append(os.path.join(path, file).replace('\\', '/'))
                    # print("不能匹配的文件：" + str(os.path.join(path, file).replace('\\', '/')))

    def save_file(self):
        """输出读取到的数据"""
        self.all_files()
        return [self.sub_folder, self.test_dir, self.no_types]


class Create_folders:
    """按照要创建的子文件列表创建文件夹文件夹"""

    def __init__(self, files_list, w_json_bool=True):
        self.files_list = files_list
        self.dirs_list = []
        self.fail_list = []
        self.no_list = []
        self.w_json_bool = w_json_bool  # 确定是否需要写json

    def new_files(self):
        """新建文件夹"""
        for files in self.files_list:
            if not os.path.exists(files):  # 判断文件夹是否已经存在，如果存在，跳过
                try:
                    os.makedirs(files, exist_ok=True)
                    # 如果想要创建的目录已经存在，也没有关系，设置exist_ok = True， 就不会引发FileExistsError
                    self.dirs_list.append(files)
                    print('创建成功:' + files)
                except Exception as eaa:
                    self.fail_list.append('创建失败：' + files + '<><><><><>错误码：' + str(eaa))
                    print('创建失败：' + files + '<><><><><>错误码：' + str(eaa))
            else:
                self.no_list.append('已存在：' + files)
                print('已存在：' + files)
        if self.w_json_bool:
            Wr_data('./js_data/创建成功的转码文件夹.json', self.dirs_list).save_paths()
            Wr_data('./js_data/创建失败的转码文件夹.json', self.fail_list).save_paths()
            Wr_data('./js_data/已创建的转码文件夹.json', self.no_list).save_paths()


class Re_names:
    """
    正则替换文件名
    :param trainpath: 源名称
    :param featurepath: 要替换的名称
    :param test: 传入的子文件夹目录或者是所有文件目录
    :param w_types: 需要更改为新的后缀,可缺省
    """

    def __init__(self, trainpath=None, featurepath=None, test=None, w_types=None):
        """
        :param trainpath: 源名称
        :param featurepath: 要替换的名称
        :param test: 传入的子文件夹目录或者是所有文件目录
        :param w_types: 需要更改为新的后缀,可缺省
        """
        if w_types is None:
            w_types = [".mp4"]
        self.trainpath = trainpath  # 源名称
        self.featurepath = featurepath  # 要替换的名称
        self.test_dir = test  # 传入的子文件夹目录或者是所有文件目录
        self.w_types = w_types  # 需要更改为新的后缀,可缺省
        self.tes = f'({self.w_types[0]})$'  # 等价('(.mp4)$')

    def re_flies(self):
        """替换文件夹路径名"""
        test_1 = re.sub(self.trainpath, self.featurepath, self.test_dir, flags=re.I)
        return test_1

    def re_flie(self):
        test_2 = re.sub(self.trainpath, self.featurepath, self.test_dir, flags=re.I)
        test_3 = re.sub(self.tes, r"", test_2, flags=re.I)
        # print(test_3)
        return test_3

    # 此方法更改后缀
    def re_puls(self):  # 重命名文件为缓存路径  传入顺序为读取 - 写入 - 待更改的内容
        test_2 = re.sub(self.trainpath, self.featurepath, self.test_dir, flags=re.I)  # 重命名文件
        a, b = os.path.splitext(str(test_2))
        # print(f"\n{b}: {a}\n{self.w_types}: {self.w_types[0]}\n{a + self.w_types[0]}\n\n")
        test_3 = str(a) + str(self.w_types[0])  # 变更后缀,更改为 return test_3 输出为路径
        return test_3

    # 此方法获取文件名
    def get_name(self):
        a, b = os.path.splitext(str(self.test_dir))
        file = os.path.basename(a + self.w_types[0])  # 无路径文件名
        return file

    # 此方法添加后缀
    def re_file_puls(self):  # 重命名文件为缓存路径  传入顺序为读取 - 写入 - 待更改的内容
        test_2 = re.sub(self.trainpath, self.featurepath, self.test_dir, flags=re.I)
        test_3 = test_2 + self.w_types[0]
        return test_3


class Compares:
    """对比输出文件差异列表"""

    def __init__(self, read_output="./视频", write_enter="./转码缓存/输出", ph_types=None,
                 w_types=None, w_json_bool=True, new_makedirs=True, exclusion=None):
        """
        :param read_output: 读取文件夹
        :param write_enter: 写入文件夹
        :param ph_types: 读取的文件类型
        :param w_types: 写入的文件后缀
        :param w_json_bool: 决定是否写入json，默认  Ture 写入状态：设置 False 则不写入
        :param new_makedirs: 默认  Ture 新建文件夹子状态：设置 False 则不新建文件夹,但不支持处理多个无后缀的同名不同类型文件
        :param exclusion: 传入存储排除数据的路径，默认为识图的排除数据路径, 设置为 1 无需排除数据
        """
        if ph_types is None:
            ph_types = [".mp4"]
        if w_types is None:
            w_types = [".mp4"]

        self.ph_types = ph_types  # 初始化文件类型
        self.w_types = w_types  # 初始化 要转码后保存的文件夹的 文件类型
        self.w_json_bool = w_json_bool  # 确定是否需要写json
        self.new_makedirs = new_makedirs  # 确定操作子文件状态

        # 读取源文件夹信息
        self.read_output = read_output  # 需要读取的路径
        self.read_files_name = './js_data/转码前子文件夹.json'  # 要写入的子文件夹路径+文件名
        self.read_file_name = "./js_data/转码前所有文件.json"  # 要存入的文件路径+文件名称

        self.read_output_files = []  # 源文件夹的所有子文件夹列表
        self.read_output_file = []  # 源文件夹的所有文件列表
        self.no_read_types = []  # 未能匹配到的文件

        # 读取源文件夹备份
        self.read_bak_output_files = []  # 源文件夹上一版备份的所有子文件夹列表
        self.read_bak_output_file = []  # 源文件夹上一版备份的所有文件列表
        self.read_different = []  # 源文件与上一版本的差异

        # 读取写入文件夹信息
        self.write_enter = write_enter  # 需要写入的路径
        self.write_files_name = './js_data/转码的子文件夹.json'  # 要写入的子文件夹路径+文件名
        self.write_file_name = './js_data/转码所有文件.json'  # 要存入的文件路径+文件名称

        self.write_output_files = []  # 写入文件夹的所有子文件夹列表
        self.write_output_file = []  # 写入文件夹的所有文件列表
        self.no_write_types = []  # 未能匹配到的文件

        # 读取排数数据的路径
        self.exclusion = exclusion

        # 源文件、缓存文件的差异
        self.wr_different = []

        # 应该删减的数据
        self.different_files = []  # 应该创建的子文件夹
        self.different_read_files = []  # 应该写入缓存的源文件
        self.different_write_file = []  # 应该删除缓存文件

    def read_fl(self):
        """读取文件夹"""

        # 检查是否生成了json数据保存文件夹
        if not os.path.exists("./js_data"):
            os.makedirs("./js_data", exist_ok=True)
            print("已经创建：./js_data")
        if not os.path.exists("./js_data/备份数据"):
            os.makedirs("./js_data/备份数据", exist_ok=True)
            print("已经创建：./js_data/备份数据")

        # 读取有问题的数据
        if self.exclusion is None:  # 默认路径
            try:
                with open('./js_data/1_要排除的数据.json', 'r', encoding='utf-8') as fl:
                    exclude_list = json.load(fl)
            except FileNotFoundError:
                exclude_list = []
        elif self.exclusion == 1:  # 无路径的情况
            print("无排除数据。")
            exclude_list = []
        else:  # 带路径的情况
            try:
                with open(self.exclusion, 'r', encoding='utf-8') as fl:
                    exclude_list = json.load(fl)
            except FileNotFoundError:
                print("路径错误！设置为无排除数据。")
                exclude_list = []

        # 读取源文件夹
        self.read_output_files, read_file, self.no_read_types = Files_read(self.read_output,
                                                                           self.ph_types).save_file()
        # 排除有问题的数据
        self.read_output_file = list(set(exclude_list) ^ set(read_file))
        # 保存原始数据
        if self.w_json_bool:
            Wr_data(self.read_files_name, self.read_output_files).save_paths()  # 保存子文件夹数据
            Wr_data(self.read_file_name, self.read_output_file).save_paths()  # 保存所有文件数据
            Wr_data('./js_data/源文件没有匹配到的文件路径.json', self.no_read_types).save_paths()  # 保存未匹配到的源文件数据

        # 读取写入文件夹的数据
        self.write_output_files, self.write_output_file, self.no_write_types = Files_read(self.write_enter,
                                                                                          self.w_types).save_file()
        if self.w_json_bool:
            Wr_data(self.write_files_name, self.write_output_files).save_paths()  # 保存子文件夹数据
            Wr_data(self.write_file_name, self.write_output_file).save_paths()  # 保存所有文件数据
            Wr_data('./js_data/转码文件夹没有匹配到的文件路径.json', self.no_write_types).save_paths()  # 保存未匹配到的源文件数据

    def difference(self):
        """比较差异，减少计算量"""

        tim = time.time()
        cache_files_read = []  # 读取子文件夹的名称正则变换为缓存路径
        cache_file_read = []  # 读取文件变换为缓存路径或不带路径的文件名
        cache_file_write = []  # 缓存文件的苏哦有文件，不带路径的文件名

        self.read_fl()
        cache_re_read = []  # cache_file_read 正则变换回读取文件路径的内容

        # 新建子文件夹
        if self.new_makedirs:
            for test_1 in self.read_output_files:  # 缓存文件夹创建没有的文件夹
                tests_re = re.sub(self.read_output, self.write_enter, test_1)
                # print(f"{test_1} >> {tests_re}")
                cache_files_read.append(tests_re)  # 正则缓存
                if tests_re not in self.write_output_files:  # 判断缓存路径是否存在文件夹
                    self.different_files.append(tests_re)
            Create_folders(self.different_files, self.w_json_bool).new_files()  # 创建文件夹

            # 获取读取和缓存文件之间的差异
            for test_2 in self.read_output_file:
                # print(f"\n{self.read_output}\n{self.write_enter}\n{test_2}")
                cache_file_read.append(Re_names(self.read_output, self.write_enter, test_2).re_file_puls())
            self.wr_different = list(set(cache_file_read) ^ set(self.write_output_file))
            if self.w_json_bool:
                Wr_data('./js_data/差异文件.json', self.wr_different).save_paths()

            # 对比文件列表，获得数据需删除列表
            self.different_write_file = list(set(self.wr_different) & set(self.write_output_file))
            for test_2_1 in self.different_write_file:  # 从差异列表中对比缓存列表，如果差异列表中存缓存数据。予以删除
                # print(test_2_1)
                bool_cache = True
                while bool_cache:
                    try:
                        os.remove(test_2_1)  # 删除无对应图片的缓存
                    except:
                        bool_cache = False
            if self.w_json_bool:
                Wr_data('./js_data/要删除的数据.json', self.different_write_file).save_paths()  # 保存需要新删除的缓存数据
            #  """
            # 对比读取文件列表，获得需生成的缓存列表 self.read_output_file self.wr_different
            for test_2_2 in self.wr_different:
                cache_re_read.append(Re_names(self.write_enter, self.read_output, test_2_2).re_flie())  # 临时变换为转码后的文件名
            self.different_read_files = list(set(cache_re_read) & set(self.read_output_file))
            if self.w_json_bool:
                Wr_data('./js_data/要缓存的数据.json', self.different_read_files).save_paths()  # 保存需要新生成的缓存数据
            #  """
            # 删除缓存路径空子文件夹
            re_dir_list_cache = []
            for test_4 in reversed(self.write_output_files):  # 倒序读取文件夹列表
                if test_4 == self.write_enter:  # 跳过最上层的文件夹的删除
                    continue
                elif test_4 not in cache_files_read:
                    print('删除文件夹：' + test_4)
                    re_dir_list_cache.append(test_4)  # 添加已删除的文件夹路径
                    os.rmdir(test_4)  # """
            if self.w_json_bool:
                Wr_data('./js_data/已删除的文件夹路径.json', re_dir_list_cache).save_paths()  # 保存已删除的文件夹路径

        # 不新建子文件夹
        else:
            # 转换文件路径
            for test_2 in self.read_output_file:
                # print(f"\n{self.read_output}\n{self.write_enter}\n{test_2}")
                cache_file_read.append(Re_names(test=test_2, w_types=self.w_types).get_name())

            for test_1 in self.write_output_file:  # 写入文件的缓存
                cache_file_write.append(Re_names(test=test_1, w_types=self.w_types).get_name())

            # 获取读取和缓存文件之间的差异
            self.wr_different = list(set(cache_file_read) ^ set(cache_file_write))
            if self.w_json_bool:
                Wr_data('./js_data/差异文件.json', self.wr_different).save_paths()

            # 对比文件列表，获得数据需删除列表
            self.different_write_file = list(set(self.wr_different) & set(cache_file_write))
            cache_name_file = []
            for test_2_1 in self.different_write_file:  # 从差异列表中对比缓存列表，如果差异列表中存缓存数据。予以删除
                file_n = self.write_enter + "/" + test_2_1
                cache_name_file.append(file_n)
                print(file_n)
                bool_cache = True
                while bool_cache:
                    try:
                        os.remove(file_n)  # 删除无对应文件的缓存
                    except:
                        bool_cache = False
            if self.w_json_bool:
                Wr_data('./js_data/要删除的数据.json', cache_name_file).save_paths()  # 保存需要新删除的缓存数据

            # 对比读取文件列表，获得需生成的缓存列表 self.read_output_file self.wr_different
            for test_3_2 in self.read_output_file:
                if Re_names(test=test_3_2, w_types=self.w_types).get_name() in self.wr_different:
                    self.different_read_files.append(test_3_2)
            if self.w_json_bool:
                Wr_data('./js_data/要缓存的数据.json', self.different_read_files).save_paths()  # 保存需要新生成的缓存数据

        print(f"耗时：{time.time() - tim:.8f} 读取文件夹: {self.read_output} ")
        return self.different_read_files  # 输出需要缓存的列表
        #  """

    def direct_results(self):
        """直接输出所需结果，不排除已存在的数据"""
        self.read_fl()

        return self.read_output_file, self.no_read_types  # 输出读取到，排除不需要的文件类型有结果，不管已存在于缓存文件夹的数据


if __name__ == '__main__':
    types1 = ['.mov', '.avi', '.m4v', '.mpg', '.ts', '.mkv', '.m2ts', '.mp4', ]
    #  types = ['.wmv']
    types = [".mp4"]
    read_folder = "./videos测试/源文件路径"
    write_folder = "./videos测试/输出文件路径"
    json_data_folder = "./json_data/"
    folder_name = "./json_data/文件夹.json"
    file_mane = "./json_data/所有文件.json"
    type_name = "./json_data/文件类型.json"

    aa = Compares(ph_types=types1, w_json_bool=False, ).difference()
    # aa = Compares(ph_types=types1, w_json_bool=False, new_makedirs=False).difference()
    print(len(aa))
    """
    a = files_read(read_folder, write_folder, types)

    print(len(a))

    print("\n\n转码失败的文件：")
    for i in a:
        print(i)
    """