# pytest 接口自动化框架

基于 `pytest` + `requests` + `YAML` 数据驱动的接口自动化测试框架，被测服务为 [DummyJSON](https://dummyjson.com)。

## 技术栈

| 组件 | 用途 |
|---|---|
| pytest | 用例收集与执行 |
| requests | 发送 HTTP 请求 |
| PyYAML | 用例数据驱动 |
| jsonpath | 响应结果提取 |
| allure-pytest | 测试报告 |

## 目录结构

```
test_project/
├── configs/
│   ├── config.ini          # 环境配置（host、数据库连接）
│   └── setting.py          # 项目路径与配置文件路径映射
├── data/                   # 用例数据（YAML）
│   ├── login.yaml          # 登录：成功 / 密码错误
│   ├── adduser.yaml        # 新增用户
│   ├── getUserlist.yaml    # 用户列表（含列表提取）
│   ├── getUser.yaml        # 用户详情（复用列表提取的 id）
│   └── userMe.yaml         # 当前登录用户（带 token / 不带 token）
├── docs/
│   ├── dummyjson-official-openapi.json   # 官方 OpenAPI 规范（68 个接口，权威来源）
│   └── dummyjson-openapi.yaml            # 精简版（仅本项目涉及的 15 个接口）
├── testcase/
│   ├── conftest.py         # 全局 fixture
│   ├── login/
│   │   └── test_login.py
│   └── userManger/
│       └── test_user_manager.py
├── unit_tools/
│   ├── apiutils.py         # 核心调度：变量替换 → 发请求 → 提取 → 断言
│   ├── assertion_utils.py  # 断言封装（code / contain / eq / ne）
│   ├── debugtalk.py        # YAML 中可调用的动态函数
│   ├── sendrequests.py     # 请求发送封装
│   ├── exception_utils/    # 自定义异常
│   └── handle_data/        # YAML / INI 解析
├── extract.yaml            # 接口间变量传递（运行时生成，已 gitignore）
├── pytest.ini              # pytest 配置
├── requirements.txt
└── run.py                  # 统一入口
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 全量执行
pytest

# 或通过入口脚本执行
python run.py

# 3. 只跑某个模块
pytest testcase/login
pytest -m login

# 4. 生成并查看 allure 报告
allure serve report/temps
```

> `userManger` 下的「当前登录用户」用例依赖登录后写入的 `accessToken`，
> 单独运行该模块前需要先执行一次 `pytest testcase/login`。

## 用例编写方式

`data/*.yaml` 中一个 `baseInfo` 对应一组接口信息，`testCase` 下可以写多条用例：

```yaml
- baseInfo:
    api_name: 登录获取 Token      # 接口名称，用于日志展示
    url: /auth/login             # 相对路径，自动拼接 config.ini 中的 host
    method: post
    header:
      Content-Type: application/json; charset=utf-8
  testCase:
    - case_name: 正确账号密码登录成功
      json:                      # 请求体：json / data / params
        username: emilys
        password: emilyspass
      validation:                # 断言配置
        - code: 200
        - eq: {'id': 1, 'username': 'emilys'}
        - ne: {'accessToken': ''}
        - contain: {'email': 'emily.johnson@x.dummyjson.com'}
      extract:                   # 提取单个值，写入 extract.yaml
        accessToken: $.accessToken
      extract_list:              # 提取列表，写入 extract.yaml
        userIds: $.users[*].id
```

### 断言模式

| 模式 | 说明 | 示例 |
|---|---|---|
| `code` | 响应状态码 | `- code: 200` |
| `eq` | 逐字段相等 | `- eq: {'id': 1}` |
| `ne` | 逐字段不相等 | `- ne: {'accessToken': ''}` |
| `contain` | 字段值包含指定字符串 | `- contain: {'message': 'Invalid credentials'}` |

字段不存在时一律判为失败，不会出现「断言没跑但显示通过」的假绿。

### 变量引用

YAML 中可以用 `${函数名(参数)}` 调用 `unit_tools/debugtalk.py` 里的方法：

| 写法 | 作用 |
|---|---|
| `${get_extract_data(accessToken)}` | 读取 `extract.yaml` 中保存的值 |
| `${get_extract_data(userIds, 1)}` | 取列表中第 1 个元素 |
| `${get_extract_data(usernames, 0)}` | 从列表中随机取一个 |
| `${get_token_header()}` | 生成 `Authorization: Bearer xxx` 请求头 |
| `${get_header(json)}` | 按参数类型生成 Content-Type |
| `${get_now_time()}` | 当前时间戳，可用于构造唯一数据 |

## 环境切换

`configs/config.ini` 中的 `[Host] host` 决定被测服务地址。YAML 里的 `url` 写相对路径，
切换测试环境时只需改这一行，无需修改任何用例数据。

## 接口文档

`docs/` 下有两份，用途不同：

| 文件 | 内容 | 来源 |
|---|---|---|
| `dummyjson-official-openapi.json` | 完整规范，68 个接口 | DummyJSON 官方 `https://dummyjson.com/openapi.json`，原样保存 |
| `dummyjson-openapi.yaml` | 精简版，仅本项目涉及的 15 个接口 | 手工整理，便于快速查阅 |

写新用例时以官方 JSON 为准。它涵盖的资源比精简版多得多，除 users / products / carts 外还有
posts、comments、todos、quotes、recipes、auth、webhook 等，且每个接口都带完整的
请求体与响应 Schema。

在线可读版：<https://dummyjson.com/docs>

> 注：DummyJSON 是模拟接口，所有写操作（POST / PUT / PATCH / DELETE）只返回一个「看起来成功」
> 的对象，不会真正落库。例如 `POST /users/add` 返回 `id: 209`，但 `GET /users/209` 是 404，
> 用户总数仍是 208。因此这类用例只能验证请求格式与响应结构，无法验证数据持久化。

## 说明

- `extract.yaml` 保存运行时的 token 等中间变量，已加入 `.gitignore`。
- 被 `demo_` 前缀标记的文件为学习过程中的练习脚本，不参与用例收集。
