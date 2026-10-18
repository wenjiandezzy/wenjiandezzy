import json
import re

import jsonpath

from unit_tools.assertion_utils import Assertions
from unit_tools.debugtalk import DebugTalk
from unit_tools.handle_data.configParser import Configparser
from unit_tools.handle_data.yaml_handle import read_yaml, write_yaml
from unit_tools.sendrequests import SendRequest

# 匹配 ${函数名(参数1, 参数2)} 形式的变量引用
VARIABLE_PATTERN = re.compile(r'\$\{(\w+)\((.*?)\)\}')

# 变量替换的最大轮数，用于防止 ${a(${b()})} 这类嵌套写法替换不干净
MAX_REPLACE_ROUND = 10

# 需要做变量替换的请求参数类型
PARAM_TYPES = ('params', 'data', 'json')


class RequestsBase:

    def __init__(self):
        self.conf = Configparser()
        self.send_request = SendRequest()
        self.asserts = Assertions()

    def build_url(self, url):
        """
        拼接完整请求地址：yaml 里写相对路径时，自动拼上 config.ini 中的 host
        :param url: yaml 中 baseInfo.url，可以是 /auth/login，也可以是完整地址
        :return: 完整 URL
        """
        if url.startswith(('http://', 'https://')):
            return url
        host = self.conf.get_host('host')
        if not host:
            raise ValueError('config.ini 中没有配置 [Host] host，无法拼接请求地址')
        return host.rstrip('/') + '/' + url.lstrip('/')

    def parse_and_replace_variables(self, yml_data):
        """
        解析并替换 yaml 数据中的变量引用，如：${get_extract_data(usernames, 0)}
        :param yml_data: 待解析的 yaml 数据（dict / list / str）
        :return: 替换完成后的数据，dict 或 list 会还原成原类型
        """
        # 字符串直接处理；dict / list 先转成 JSON 字符串，方便统一做文本替换
        yml_data_str = yml_data if isinstance(yml_data, str) else json.dumps(yml_data, ensure_ascii=False)
        print(f'[变量替换] 解析前：{yml_data_str}')

        def _replace(match):
            func_name, func_params = match.group(1), match.group(2)
            params = [p.strip().strip('\'"') for p in func_params.split(',') if p.strip()]

            func = getattr(DebugTalk(), func_name, None)
            if func is None:
                raise AttributeError(f'debugtalk.py 中不存在函数 {func_name}，请检查 yaml 中的变量写法')

            result = func(*params)
            print(f'[变量替换] {func_name}{tuple(params)} -> {result!r}')

            # 非字符串结果（dict / list / int）转成 JSON 文本，保证后面 json.loads 能正确还原
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)

        # 用正则替换而不是手动 index 截取：
        # 既不会因为字符串里先出现普通 $（如价格 "$100"）而取错起点，
        # 也能一次替换掉多个变量。
        for _ in range(MAX_REPLACE_ROUND):
            new_str = VARIABLE_PATTERN.sub(_replace, yml_data_str)
            if new_str == yml_data_str:
                break
            yml_data_str = new_str

        # 还原成 dict / list，还原失败说明原文本来就是普通字符串
        try:
            return json.loads(yml_data_str)
        except (json.JSONDecodeError, TypeError):
            return yml_data_str

    def execute_test_cases(self, api_info):
        """
        规范 yaml 接口信息，执行接口、提取结果以及断言操作
        :param api_info: yaml 里的一个接口信息（含 baseInfo 和 testCase）
        :return:
        """
        base_info = api_info['baseInfo']
        api_name = base_info['api_name']
        method = base_info['method']
        url = self.build_url(self.parse_and_replace_variables(base_info['url']))

        header = self.parse_and_replace_variables(base_info['header']) if base_info.get('header') else None
        cookies = self.parse_and_replace_variables(base_info['cookies']) if base_info.get('cookies') else None

        for testcase in api_info['testCase']:
            # 先把框架自己用的字段取出来，剩下的才是要发给接口的参数
            case_name = testcase.pop('case_name', '未命名用例')
            validation = testcase.pop('validation', None)
            extract = testcase.pop('extract', None)
            extract_list = testcase.pop('extract_list', None)

            print(f'\n========== 用例：{api_name} / {case_name} ==========')
            if validation is None:
                raise ValueError(f'用例【{case_name}】缺少 validation 配置，无法执行断言')

            # 断言里的变量引用（比如 eq 预期值要取 extract.yaml 的数据）先替换
            validation = self.parse_and_replace_variables(validation)

            # 请求参数里的变量引用替换
            for param_type in list(testcase.keys()):
                if param_type in PARAM_TYPES:
                    testcase[param_type] = self.parse_and_replace_variables(testcase[param_type])

            response = self.send_request.execute_api_request(
                api_name=api_name,
                url=url,
                method=method,
                header=header,
                case_name=case_name,
                cookie=cookies,
                file=None,
                **testcase
            )

            if response is None:
                raise RuntimeError(f'用例【{case_name}】请求失败，未拿到任何响应')

            print(f'[响应] 状态码：{response.status_code}')
            print(f'[响应] 内容：{response.text[:500]}')

            # 处理接口返回值提取（先提取，断言里可能要用到）
            if extract:
                self.extract_data(extract, response.text)
            if extract_list:
                self.extract_data_list(extract_list, response.text)

            # 处理接口断言
            try:
                response_json = response.json()
            except ValueError:
                response_json = {}
            self.asserts.assert_result(validation, response_json, response.status_code)

    @classmethod
    def extract_data(cls, testcase_extract, response_text):
        """
        提取单个参数，支持 jsonpath 提取和正则表达式提取
        :param testcase_extract: (dict) yaml 中的 extract，例如 {'accessToken': '$.accessToken'}
        :param response_text: (str) 接口的实际返回值
        :return:
        """
        for key, value in testcase_extract.items():
            result = cls._extract_single(key, value, response_text)
            if result is None:
                continue
            write_yaml({key: result})

    @classmethod
    def extract_data_list(cls, testcase_extract, response_text):
        """
        提取多个参数（返回列表），支持 jsonpath 提取和正则表达式提取
        :param testcase_extract: (dict) yaml 中的 extract_list，例如 {'userIds': '$.users[*].id'}
        :param response_text: (str) 接口的实际返回值
        :return:
        """
        for key, value in testcase_extract.items():
            result = cls._extract_single(key, value, response_text, return_list=True)
            if result is None:
                continue
            write_yaml({key: result})

    @classmethod
    def _extract_single(cls, key, expression, response_text, return_list=False):
        """
        执行单条提取逻辑，提取失败时打印原因并返回 None，不让异常冒到用例层
        :param key: 提取后写入 extract.yaml 的变量名
        :param expression: jsonpath 或正则表达式
        :param response_text: 接口原始返回文本
        :param return_list: True 时返回列表（extract_list），False 时返回单个值（extract）
        :return: 提取结果，失败返回 None
        """
        # 以 $ 开头的当作 jsonpath 表达式
        if expression.strip().startswith('$'):
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError:
                print(f'[extract] {key} 提取失败：响应不是合法 JSON，无法使用 jsonpath')
                return None

            try:
                result = jsonpath.jsonpath(response_json, expression)
            except Exception as e:
                print(f'[extract] {key} 提取失败：jsonpath 表达式 {expression} 解析出错，原因：{e}')
                return None

            if not result:
                print(f'[extract] {key} 提取失败：jsonpath 表达式 {expression} 未匹配到数据')
                return None
            return result if return_list else result[0]

        # 否则当作正则表达式
        try:
            if return_list:
                result = re.findall(expression, response_text, re.S)
                if not result:
                    print(f'[extract] {key} 提取失败：正则 {expression} 未匹配到内容')
                    return None
                return result

            match = re.search(expression, response_text)
            if match is None:
                print(f'[extract] {key} 提取失败：正则 {expression} 未匹配到内容')
                return None
            group = match.group(1) if match.groups() else match.group(0)
            return int(group) if group.isdigit() else group
        except re.error as e:
            print(f'[extract] {key} 提取失败：正则表达式 {expression} 有语法错误，原因：{e}')
            return None


if __name__ == '__main__':
    from configs.setting import FILE_PATH

    req = RequestsBase()
    req.execute_test_cases(read_yaml(FILE_PATH['login'])[0])
