import yaml

from configs.setting import FILE_PATH


def read_yaml(yaml_path):
    """
    读取 yaml 文件数据
    :param yaml_path: 文件路径
    :return: 解析后的数据（通常是 list 或 dict）
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except UnicodeDecodeError:
        # 不再返回 None：返回 None 会让 pytest 的 parametrize 报出难以定位的 TypeError
        raise ValueError(f'yaml 文件编码错误：{yaml_path}，请确认文件为 UTF-8 编码')
    except FileNotFoundError:
        raise FileNotFoundError(f'yaml 文件不存在：{yaml_path}')
    except yaml.YAMLError as e:
        raise ValueError(f'yaml 文件格式错误：{yaml_path}，原因：{e}')


def write_yaml(value, mode='a'):
    """
    向 extract.yaml 写入数据
    :param value: (dict) 写入的数据，必须为字典类型
    :param mode: 'a' 追加（与已有数据合并），'w' 覆盖
    :return:
    """
    if not isinstance(value, dict):
        print('[yaml] 写入的数据类型必须为字典')
        return

    file_path = FILE_PATH['extract']
    try:
        if mode == 'a':
            # 追加：先读已有数据，合并后再整体写回
            # 直接以 'a' 模式 dump 会产生重复 key，导致 yaml 解析异常
            existing = {}
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    existing = loaded
            except FileNotFoundError:
                pass

            existing.update(value)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing, f, allow_unicode=True, sort_keys=False)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(value, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        print(f'[yaml] 写入 {file_path} 失败，原因：{e}')


def clear_yaml():
    """
    清空 extract.yaml（每次全量执行前调用，避免上一次的脏数据影响本次）
    :return:
    """
    with open(FILE_PATH['extract'], 'w', encoding='utf-8') as f:
        f.truncate()


def get_extract_yaml(node_name):
    """
    获取 extract.yaml 中某个 key 的值
    :param node_name: extract.yaml 中的 key，如 accessToken、usernames
    :return: 对应的值，取不到返回 None
    """
    file_path = FILE_PATH['extract']
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            extract_data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f'[yaml] extract.yaml 不存在：{file_path}')
        return None
    except Exception as e:
        print(f'[yaml] 读取 {file_path} 失败，原因：{e}')
        return None

    if not isinstance(extract_data, dict):
        return None
    return extract_data.get(node_name)


if __name__ == '__main__':
    print(get_extract_yaml('accessToken'))
