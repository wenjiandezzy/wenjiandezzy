import pytest

from configs.setting import FILE_PATH
from unit_tools.apiutils import RequestsBase
from unit_tools.handle_data.yaml_handle import read_yaml

# 列表顺序就是执行顺序，不能随意调整：
# getUserlist 先跑并提取 userIds，getUser 才能用 ${get_extract_data(userIds, 1)} 拼 url
USER_API_FILES = [
    ('新增用户', FILE_PATH['adduser']),
    ('用户列表', FILE_PATH['getUserlist']),
    ('用户详情', FILE_PATH['getUser']),
    ('当前登录用户', FILE_PATH['userMe']),
]


class TestUserManager:
    """用户管理模块：新增、列表、详情、当前登录用户"""

    @pytest.mark.api
    @pytest.mark.parametrize(
        'api_name, yaml_path',
        USER_API_FILES,
        ids=[name for name, _ in USER_API_FILES],
    )
    def test_user_manager(self, api_name, yaml_path):
        req = RequestsBase()
        # 一个 yaml 里可以写多组 baseInfo（比如已认证 / 未认证），逐个执行
        for api_info in read_yaml(yaml_path):
            req.execute_test_cases(api_info)
