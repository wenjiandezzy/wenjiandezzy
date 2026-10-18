import sys

import pytest

if __name__ == '__main__':
    # 支持传参，例如：python run.py testcase/login -v
    # 不传参时走 pytest.ini 里的 addopts 和 testpaths
    sys.exit(pytest.main(sys.argv[1:]))
