import socket
import paramiko
import os
import subprocess
from tool.config_variables import tpydataPath, outputCleanPath, djSrcPath, mutantsFilePath, faliingTestOutputPath, faultlocalizationResultPath, SOMfaultlocalizationResultPath, sbflMethod, sourcePath, password, project



def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]

ip = get_host_ip()

def sftp_upload(hostname, username, password, localpath, remotepath):
    """
    通过 SFTP 协议上传文件或文件夹
    :param hostname: 远程主机 IP
    :param username: 登录用户名
    :param password: 登录密码
    :param localpath: 本地文件或文件夹路径
    :param remotepath: 远程文件或文件夹路径
    :return: 无返回值
    """
    transport = None
    sftp = None

    try:
        transport = paramiko.Transport((hostname, 22))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # 判断本地路径是文件还是文件夹
        if os.path.isfile(localpath):
            # 上传单个文件
            sftp.put(localpath, remotepath)
            print(f"上传文件 {localpath} 到 {remotepath} 成功！")
        elif os.path.isdir(localpath):
            # 递归上传文件夹
            parent_remote_path = remotepath.rstrip('/')
            parent_local_path = localpath.rstrip('/')
            for root, dirs, files in os.walk(localpath):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    remote_file_path = os.path.join(parent_remote_path, os.path.relpath(local_file_path, parent_local_path))
                    remote_file_path = remote_file_path.replace("\\", "/")
                    sftp.put(local_file_path, remote_file_path)
                    print(f"上传文件 {local_file_path} 到 {remote_file_path} 成功！")
        else:
            print(f"本地路径 {localpath} 不是文件也不是文件夹！")

        print("上传完成！")
    except paramiko.AuthenticationException:
        print('认证失败，请检查用户名和密码。')
    except paramiko.SSHException as e:
        print(f'SFTP连接或上传过程中出现SSH错误: {e}')
    except IOError as e:
        print(f'本地文件读取失败: {e}')
    except Exception as e:
        print(f'出现错误: {e}')
    finally:
        # 关闭连接
        if sftp:
            sftp.close()
        if transport:
            transport.close()


# 使用scp命令从30服务器上下载临时文件
def cp_from_remote(projectDir, versionDir):
    source_paths = [
        (os.path.join(djSrcPath, projectDir, versionDir), os.path.join(djSrcPath, projectDir)),
        (os.path.join(outputCleanPath, projectDir, versionDir), os.path.join(outputCleanPath, projectDir)),
        (os.path.join(tpydataPath, projectDir, versionDir), os.path.join(tpydataPath, projectDir)),
        (os.path.join(faliingTestOutputPath, projectDir, versionDir), os.path.join(faliingTestOutputPath, projectDir))
    ]

    for source_path, destination_path in source_paths:
        os.makedirs(destination_path, exist_ok=True)
        cmd = f'sshpass -p {password} scp -o StrictHostKeyChecking=no -r {"fanluxi"}@{"202.4.130.30"}:{source_path} {destination_path}'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return False

    return True