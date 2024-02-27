import logging
def logger_config(log_path):
    """
    配置日志记录器
    :param log_path: 日志输出路径
    :return: 日志记录器对象
    """
    # 创建日志记录器对象
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置日志记录器的全局日志级别为DEBUG

    # 创建文件处理器，将日志写入文件
    file_handler = logging.FileHandler(log_path, encoding='UTF-8')
    file_handler.setLevel(logging.INFO)  # 设置文件处理器的日志级别为INFO

    # 创建格式化器，定义日志的格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)  # 将格式化器应用于文件处理器

    # 创建流处理器，将日志输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 设置流处理器的日志级别为DEBUG

    # 将文件处理器和流处理器添加到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger