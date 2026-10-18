import json

import jsonpath

from unit_tools.exception_utils.exceptions import AssertTypeError


class Assertions:
    """
    接口断言模式封装
    1. code    状态码断言
    2. contain 包含断言（字段值中包含指定字符串）
    3. eq      相等断言
    4. ne      不相等断言

    每个断言方法都返回「失败条数」，由 assert_result 汇总后统一断言，
    这样可以一次跑完全部断言、看全量差异，而不是第一个失败就中断。
    """

    _MISSING = object()

    @classmethod
    def status_code_assert(cls, expected_result, status_code):
        """
        接口的响应状态码断言
        :param expected_result: yaml 中 code 模式的预期状态码
        :param status_code: 接口实际返回的状态码
        :return: 失败条数
        """
        if int(expected_result) == int(status_code):
            print(f'[code] 断言成功：{status_code} == {expected_result}')
            return 0
        print(f'[code] 断言失败：{status_code} != {expected_result}')
        return 1

    @classmethod
    def contain_assert(cls, expected_result, response):
        """
        包含模式断言：预期字符串是否出现在响应对应字段的值中
        :param expected_result: (dict) yaml 中 contain 模式的数据，如 {'message': 'Invalid credentials'}
        :param response: (dict) 接口实际响应 JSON
        :return: 失败条数
        """
        failure_count = 0
        for assert_key, assert_value in expected_result.items():
            response_list = jsonpath.jsonpath(response, f'$..{assert_key}')
            # 字段根本不存在时必须判失败，否则就是「假绿」
            if not response_list:
                failure_count += 1
                print(f'[contain] 断言失败：响应中不存在字段 {assert_key}')
                continue

            # 逐个匹配到的值单独比对，避免把多个字段拼在一起后产生跨字段的误匹配
            actual_values = [
                item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
                for item in response_list
            ]
            if any(str(assert_value) in value for value in actual_values):
                print(f'[contain] 断言成功：{assert_value} 存在于 {actual_values} 中')
            else:
                failure_count += 1
                print(f'[contain] 断言失败：{assert_value} 不存在于 {actual_values} 中')
        return failure_count

    @classmethod
    def equal_assert(cls, expected_result, response):
        """
        相等断言：逐个字段比对，字段缺失也算失败
        :param expected_result: (dict) yaml 中 eq 模式的数据
        :param response: (dict) 接口实际响应 JSON
        :return: 失败条数
        """
        failure_count = 0
        if not isinstance(response, dict):
            print(f'[eq] 断言失败：响应不是字典类型，无法逐字段比对（实际类型 {type(response).__name__}）')
            return 1

        for key, expected in expected_result.items():
            actual = response.get(key, cls._MISSING)
            if actual is cls._MISSING:
                failure_count += 1
                print(f'[eq] 断言失败：响应中不存在字段 {key}')
            elif actual != expected:
                failure_count += 1
                print(f'[eq] 断言失败：{key} 实际 {actual!r} != 预期 {expected!r}')
            else:
                print(f'[eq] 断言成功：{key} == {expected!r}')
        return failure_count

    @classmethod
    def not_equal_assert(cls, expected_result, response):
        """
        不相等断言：逐个字段比对，字段缺失也算失败（无法证明「不相等」）
        :param expected_result: (dict) yaml 中 ne 模式的数据
        :param response: (dict) 接口实际响应 JSON
        :return: 失败条数
        """
        failure_count = 0
        if not isinstance(response, dict):
            print(f'[ne] 断言失败：响应不是字典类型，无法逐字段比对（实际类型 {type(response).__name__}）')
            return 1

        for key, expected in expected_result.items():
            actual = response.get(key, cls._MISSING)
            if actual is cls._MISSING:
                failure_count += 1
                print(f'[ne] 断言失败：响应中不存在字段 {key}')
            elif actual == expected:
                failure_count += 1
                print(f'[ne] 断言失败：{key} 实际 {actual!r} 与预期 {expected!r} 相等')
            else:
                print(f'[ne] 断言成功：{key} 实际 {actual!r} != 预期 {expected!r}')
        return failure_count

    @classmethod
    def assert_result(cls, expected_result, response, status_code):
        """
        断言主函数，汇总所有断言模式的失败条数，为 0 才算通过
        :param expected_result: (list) yaml 中 validation 下的预期结果
        :param response: 接口实际响应 JSON（dict）
        :param status_code: 接口实际响应状态码
        :return:
        """
        if not expected_result:
            raise ValueError('validation 断言配置为空，请在 yaml 的 testCase 中补充 validation')

        # 兼容误写成字典的情况，统一转成列表处理
        if isinstance(expected_result, dict):
            expected_result = [expected_result]
        if not isinstance(expected_result, list):
            raise TypeError(f'validation 必须是 list，当前为 {type(expected_result).__name__}')

        assert_methods = {
            'code': cls.status_code_assert,
            'contain': cls.contain_assert,
            'eq': cls.equal_assert,
            'ne': cls.not_equal_assert,
        }

        all_flag = 0
        for single_validation in expected_result:
            if not isinstance(single_validation, dict):
                raise TypeError(f'validation 列表中的每一项必须是字典，当前为 {type(single_validation).__name__}')
            for assert_mode, assert_value in single_validation.items():
                assert_method = assert_methods.get(assert_mode)
                if assert_method is None:
                    raise AssertTypeError(f'不支持的断言模式：{assert_mode}，可用模式：{list(assert_methods)}')

                if assert_mode == 'code':
                    all_flag += assert_method(assert_value, status_code)
                else:
                    all_flag += assert_method(assert_value, response)

        assert all_flag == 0, f'断言失败，共 {all_flag} 项未通过'
        print('[assert] 全部断言通过')
