import random
import re
import time

from unit_tools.handle_data.yaml_handle import get_extract_yaml


class DebugTalk:
    """
    YAML 用例里可以通过 ${函数名(参数)} 直接调用的动态函数库。

    例如 yaml 中写：
        username: ${get_extract_data(usernames, 0)}
        header:   ${get_token_header()}
    框架在 parse_and_replace_variables 里用 getattr 反射调用这里的方法。
    """

    def get_extract_data(self, node_name, out_format=None):
        """
        获取 extract.yaml 中保存的数据
        :param node_name: extract.yaml 中的 key，如 accessToken、usernames
        :param out_format: 仅对列表类型的数据生效
                           0  -> 随机取一个
                           -1 -> 全部取出，用逗号拼成字符串
                           -2 -> 全部取出，保持列表
                           正数 -> 按顺序取第 n 个（从 1 开始）
        :return: 取到的数据，取不到返回 None
        """
        data = get_extract_yaml(node_name)
        if data is None:
            print(f'[debugtalk] extract.yaml 中未找到 {node_name}')
            return None

        # 普通字符串 / 数字直接返回，不需要处理 out_format
        if not isinstance(data, list):
            return data

        if out_format is None:
            return data

        # yaml 里传进来的参数都是字符串，先判断是不是整数再转换
        if not re.match(r'^[+-]?\d+$', str(out_format)):
            print(f'[debugtalk] out_format 只支持整数，收到的是 {out_format!r}，已忽略')
            return data

        out_format = int(out_format)
        if out_format == 0:
            return random.choice(data)
        if out_format == -1:
            return ','.join(map(str, data))
        if out_format == -2:
            return [str(item) for item in data]

        # 按顺序读取（索引从 1 开始）
        if 0 < out_format <= len(data):
            return data[out_format - 1]
        print(f'[debugtalk] 索引 {out_format} 越界，当前列表长度 {len(data)}')
        return None

    def get_now_time(self):
        """获取当前时间戳，可用于构造唯一数据"""
        return time.time()

    def get_header(self, params_type):
        """
        按参数类型返回对应的请求头
        :param params_type: data 或 json
        :return: 请求头字典
        """
        header_mapping = {
            'data': {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
            'json': {'Content-Type': 'application/json; charset=utf-8'},
        }
        header = header_mapping.get(params_type)
        if header is None:
            raise ValueError(f'不支持的请求头类型：{params_type}，只支持 data / json')
        return header

    def get_token_header(self):
        """
        从 extract.yaml 取出登录后保存的 accessToken，拼成带认证信息的请求头
        :return: {'Authorization': 'Bearer xxx'}
        """
        token = get_extract_yaml('accessToken')
        if not token:
            raise ValueError(
                'extract.yaml 中没有 accessToken，请先执行 testcase/login 下的登录用例来获取 token'
            )
        return {'Authorization': f'Bearer {token}'}


if __name__ == '__main__':
    debug = DebugTalk()
    print(debug.get_extract_data('usernames', -2))
