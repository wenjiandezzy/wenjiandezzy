class AssertTypeError(Exception):
    """
    yaml文件断言模式类型错误异常
    """
    def __init__(self, msg='不支持该模式断言'):
        self.msg = msg
        super(AssertTypeError, self).__init__(self.msg)