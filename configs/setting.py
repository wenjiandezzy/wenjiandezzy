import os
import sys

# 项目根目录（configs 的上一级）
DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 把项目根目录加入 sys.path，保证单独运行某个模块时也能 import 到 configs / unit_tools
if DIR_PATH not in sys.path:
    sys.path.append(DIR_PATH)

DATA_PATH = os.path.join(DIR_PATH, 'data')
REPORT_PATH = os.path.join(DIR_PATH, 'report')

FILE_PATH = {
    # 配置文件
    'ini': os.path.join(DIR_PATH, 'configs', 'config.ini'),
    # 接口间变量传递（token 等），运行时生成，不进版本库
    'extract': os.path.join(DIR_PATH, 'extract.yaml'),
    # 用例数据
    'login': os.path.join(DATA_PATH, 'login.yaml'),
    'adduser': os.path.join(DATA_PATH, 'adduser.yaml'),
    'getUserlist': os.path.join(DATA_PATH, 'getUserlist.yaml'),
    'getUser': os.path.join(DATA_PATH, 'getUser.yaml'),
    'userMe': os.path.join(DATA_PATH, 'userMe.yaml'),
}
