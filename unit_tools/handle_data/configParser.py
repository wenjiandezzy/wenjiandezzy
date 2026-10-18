import configparser
from configs.setting import FILE_PATH


class Configparser:
    """
    解析.ini后缀的配置文件
    """

    def __init__(self, file_path=FILE_PATH['ini']):
        self.file_path = file_path
        self.config = configparser.ConfigParser()
        self.read_config()

    def read_config(self):
        # 必须显式指定 utf-8：config.ini 里有中文注释，
        # 不指定时 configparser 会用系统默认编码（中文 Windows 是 GBK）导致 UnicodeDecodeError
        self.config.read(self.file_path, encoding='utf-8')

    def get_value(self, section, option):
        """
        获取配置文件的值
        :param section: 头参数
        :param option: 下级参数key值
        :return:
        """

        try:
            return self.config.get(section, option)
        except Exception as e:
            print(f'解析配置文件出现错误，原因：{e}')

    def get_host(self,option):
        """
        专门获取接口的服务器ip地址信息
        :param option:
        :return:
        """
        return self.get_value('Host', option)

    def get_mysql_conf(self, option):
        """
        获取MySQL数据库的配置参数值
        :return:
        """
        return self.get_value('Mysql', option)

if __name__ == '__main__':
    conf = Configparser()
    res = conf.get_host('host')
    # res = conf.get_mysql_conf('port')
    print(res)
