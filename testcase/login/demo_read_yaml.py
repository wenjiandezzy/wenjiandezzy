from configs.setting import FILE_PATH
from unit_tools.handle_data.yaml_handle import read_yaml

yaml_path = FILE_PATH['login']
data_list = read_yaml(yaml_path)
api_info = data_list[0]
print('处理之前：', api_info)
# login.yaml 里请求体用的是 json 字段（不是 data）
req_param = api_info['testCase'][0]['json']
print('处理之后：', req_param)
