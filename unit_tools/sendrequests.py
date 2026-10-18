import requests


class SendRequest:
    """
    接口请求封装
    统一收口超时、证书校验、cookie 提取等公共逻辑，用例层不用关心 requests 的细节。
    """

    def __init__(self, timeout=10, verify=True):
        # 复用 Session：同一个实例内会自动带上服务端下发的 cookie
        self.session = requests.Session()
        self.timeout = timeout
        self.verify = verify

    def execute_api_request(self, api_name, url, method, header, case_name,
                            cookie=None, file=None, **kwargs):
        """
        发起接口请求
        :param api_name: 接口名称（仅用于日志和报告展示）
        :param url: 接口地址
        :param method: 请求方法，get / post / put / delete ...
        :param header: 请求头
        :param case_name: 测试用例名称（仅用于日志和报告展示）
        :param cookie: cookie，字典格式
        :param file: 文件上传，requests 的 files 参数
        :param kwargs: 其他请求参数，如 json / data / params / timeout / verify
        :return: requests.Response 对象；请求异常时返回 None
        """
        # 允许单条用例覆盖全局的超时和证书校验设置
        timeout = kwargs.pop('timeout', self.timeout)
        verify = kwargs.pop('verify', self.verify)

        print(f'[请求] {method.upper()} {url}')
        print(f'[请求] header={header}')
        print(f'[请求] params={kwargs}')

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=header,
                cookies=cookie,
                files=file,
                timeout=timeout,
                verify=verify,
                **kwargs
            )
        except requests.exceptions.ConnectionError:
            print(f'[请求异常] {api_name} / {case_name}：连接失败，请检查网络或服务是否启动')
            return None
        except requests.exceptions.Timeout:
            print(f'[请求异常] {api_name} / {case_name}：请求超时（{timeout}s）')
            return None
        except requests.exceptions.RequestException as e:
            print(f'[请求异常] {api_name} / {case_name}：{e}')
            return None

        return response
