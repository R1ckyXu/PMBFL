import os
import shutil
import subprocess
import sys
import signal
# 清空目录（包括非空目录）
def clearDir(Path):
    if os.path.exists(Path):
        shutil.rmtree(Path, ignore_errors=True)


# 自动创建不存在的目录
def checkAndCreateDir(Path):
    if not os.path.exists(Path):
        os.mkdir(Path)


def run(cmd, shell=False):
    """
    开启子进程，执行对应指令，控制台打印执行过程，然后返回子进程执行的状态码和执行返回的数据
    :param cmd: 子进程命令
    :param shell: 是否开启shell
    :return: 子进程状态码和执行结果
    """
    print('\033[1;32m************** START **************\033[0m')

    p = subprocess.Popen(
        cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = []
    while p.poll() is None:
        line = p.stdout.readline().strip()
        if line:
            line = _decode_data(line)
            result.append(line)
            print('\033[1;35m{0}\033[0m'.format(line))
            if 'mutate' in line:
                # 清空缓存
                sys.stdout.flush()
                sys.stderr.flush()
                break
        # 清空缓存
        sys.stdout.flush()
        sys.stderr.flush()
    if p.poll is None:
        os.killpg(p.pid, signal.SIGTERM)
    # 判断返回码状态
    if p.returncode == 0:
        print('\033[1;32m************** SUCCESS **************\033[0m')
    else:
        print('\033[1;31m************** FAILED **************\033[0m')
    return p.returncode, '\r\n'.join(result)


def _decode_data(byte_data: bytes):
    """
    解码数据
    :param byte_data: 待解码数据
    :return: 解码字符串
    """
    try:
        return byte_data.decode('UTF-8')
    except UnicodeDecodeError:
        return byte_data.decode('GB18030')
