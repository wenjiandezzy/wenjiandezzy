import pytest

from configs.setting import FILE_PATH
from unit_tools.apiutils import RequestsBase
from unit_tools.handle_data.yaml_handle import read_yaml

# 模块加载时就读取 yaml，parametrize 的 ids 也要用，所以提到模块级
LOGIN_API_LIST = read_yaml(FILE_PATH['login'])


class TestLogin:
    """登录模块：覆盖登录成功与密码错误两种场景，并提取 token 供后续用例使用"""

    @pytest.mark.api
    @pytest.mark.login
    @pytest.mark.parametrize(
        'api_info',
        LOGIN_API_LIST,
        ids=[item['baseInfo']['api_name'] for item in LOGIN_API_LIST],
    )
    def test_login_module(self, api_info):
        RequestsBase().execute_test_cases(api_info)
