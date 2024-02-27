import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, wait
import os
import shutil
import uuid
import json
from threading import Thread
import sys
import subprocess
import signal
from tool.config_variables import tempSrcPath, tpydataPath, outputCleanPath, djSrcPath, mutantsFilePath, faliingTestOutputPath, faultlocalizationResultPath, SOMfaultlocalizationResultPath, sbflMethod, sourcePath, password, project
result = 0

def compile(programDir, self):
    cmd = ['{}/framework/bin/defects4j'.format(self.configData['D4jHome']), 'compile', '-w', programDir]
    
    # 使用preexec_fn设置子进程组
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    try:
        stdout, stderr = process.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        # 使用os.killpg发送信号到子进程组
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        
        self.status = 0
        print('编译超时，杀死进程')
        return False
    except Exception as e:
        # 处理其他可能的异常
        print(f"发生异常: {e}")
        self.status = 0
        return False

    if process.returncode != 0:
        self.status = 0
        print('编译失败')
        return False

    return True

def test(programDir, self):
    cmd = ['{}/framework/bin/defects4j'.format(self.configData['D4jHome']), 'test', '-w', programDir]
    
    # 使用preexec_fn设置子进程组
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    try:
        stdout, stderr = process.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        # 使用os.killpg发送信号到子进程组
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        
        self.status = 0
        print('测试超时，杀死进程')
        return False
    except Exception as e:
        # 处理其他可能的异常
        print(f"发生异常: {e}")
        self.status = 0
        return False

    if process.returncode != 0:
        self.status = 0
        print('测试失败')
        return False

    self.status = 1
    return True


# def compile(programeDir, self):
#     # print('开始编译')
#     # 执行d4j自带的编译脚本
#     cmd = ['{}/framework/bin/defects4j'.format(self.configData['D4jHome']), 'compile', '-w', programeDir]
#     completed_process = None
#     try:
#         with open('logs/d4jCompile.log', 'a') as log_file:
#             completed_process = subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT, check=True, timeout=360)

#     except subprocess.TimeoutExpired:
#         self.status = 0
#         print('编译超时，杀死进程')
#         if completed_process is not None:
#             completed_process.terminate()
#             completed_process.kill()
#         return False

#     except subprocess.CalledProcessError:
#         self.status = 0
#         print('编译失败')
#         return False

#     return True


# def test(programeDir, self):
#     # 执行d4j自带的测试脚本
#     cmd = ['{}/framework/bin/defects4j'.format(self.configData['D4jHome']), 'test', '-w', programeDir]
#     completed_process = None
#     try:
#         with open('logs/d4jTest.log', 'a') as log_file:
#             completed_process = subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT, check=True, timeout=360)

#     except subprocess.TimeoutExpired:
#         self.status = 0
#         print('测试超时，杀死进程')
#         if completed_process is not None:
#             completed_process.terminate()
#             completed_process.kill()
#         # os.killpg(os.getpgid(completed_process.pid), signal.SIGTERM)
#         return False

#     except subprocess.CalledProcessError:
#         self.status = 0
#         print('测试失败')
#         return False

#     self.status = 1
#     return True


def checkAndCreateDir(Path):
    if not os.path.exists(Path):
        os.mkdir(Path)

def checkAndCleanDir(Path):
    try:
        shutil.rmtree(Path)
    except OSError as e:
        print("Error: %s : %s" % (Path, e.strerror))
    os.mkdir(Path)

class Executor:
    def __init__(self, project, version, muInfo,configData):
        
        # with open('../config.json', 'r') as configFile:
        #     # print('开始读取配置文件')
        #     self.configData = json.load(configFile)
        #     # print('读取配置文件完成')
        self.configData = configData
        # 原始错误程序失败测试用例结果路径
        self.faliingTestOutputPath = self.configData['faliingTestOutputPath']
        # metalix方法
        self.passList = {
                'type1': [],
                'type2': [],
                'type3': [],
                'type4': []}
        self.killList = {
                'type1': [],
                'type2': [],
                'type3': [],
                'type4': []}
        # MUSE方法
        self.mKillList = {}

        # 完整代码的具体版本路径
        self.djSrcPath = os.path.join(self.configData['djSrcPath'], project, version)
        self.tempSrcPath = self.configData['tempSrcPath']
        
        checkAndCreateDir(self.tempSrcPath)
        
        # 项目名称
        self.project = project
        # 项目id
        self.version = version
        
        # 线程锁
        self.OccupiedVersionMutex = threading.Lock()

        self.innerTempSrcPath = ''
        self.muInfo = muInfo
        self.status = 0

        # 如果变异体执行结果存在
        # if os.path.exists(faultlocalizationResultPath + '/' + project + '/' + version + '/failing_tests/' + str(self.muInfo["index"])):
        #     try:
        #         self.start_save()
        #     except Exception as e:
        #         exc_type, exc_obj, exc_tb = sys.exc_info()
        #         line_number = exc_tb.tb_lineno
        #         file_name = exc_tb.tb_frame.f_code.co_filename
        #         print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
        #         self.status = 0
        #     finally:
        #         return
        # else:
        try:
            self.start_copy()  # 把指定版本整体复制到tmp文件夹
            self.start_muti()  # 仅替换变异体文件，该版本的其他文件不变
            self.start_compile_run()
            self.start_remove()
            self.status = 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            line_number = exc_tb.tb_lineno
            file_name = exc_tb.tb_frame.f_code.co_filename
            print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
            self.status = 0
            self.start_remove()


    def start_copy(self):
        # print("-------start copy", self.project, self.version, "-------")
        # 随机生成字符串
        uid = str(uuid.uuid4())
        suid = ''.join(uid.split('-'))
        self.innerTempSrcPath = os.path.join(self.tempSrcPath, self.project+"-"+self.version+"-"+suid)

        self.OccupiedVersionMutex.acquire()
        shutil.copytree(self.djSrcPath, self.innerTempSrcPath)
        self.OccupiedVersionMutex.release()
        # print("-------copy end-------")

    def start_muti(self):
        # print("-------mutation build-------")
        self.OccupiedVersionMutex.acquire()
        shutil.copyfile(self.muInfo['mutFilePath'], os.path.join(self.innerTempSrcPath,self.muInfo['relativePath']))
        self.OccupiedVersionMutex.release()
        # print("-------mutation build ebd-------")

    def start_compile_run(self):
        # print("-------start compile run-------")

        # 以下需要重写
        try:
            # 变异体的失败测试用例
            faileTests = {
                'type1': [],
                'type2': [],
                'type3': [],
                'type4': []
            }
            # 原始程序的失败测试用例
            originFaileTests = {
                'type1': [],
                'type2': [],
                'type3': [],
                'type4': []
            }
            # 获取所有的测试用例
            with open(os.path.join(outputCleanPath, self.project, self.version, "all_tests.txt"), 'r', encoding='utf-8') as f:
                allTests = [line.replace("#","::").strip() for line in f.readlines()]
            
            if not os.path.exists(os.path.join(faultlocalizationResultPath, self.project, self.version, "failing_tests", str(self.muInfo["index"]))):
                # print("-------start compile run-------")
                if not compile(self.innerTempSrcPath, self):
                    return
                
                if not test(self.innerTempSrcPath, self):
                    return


                # 把变异体的执行结果存到FOMResult里面去
                # 之所以djSrc-temp里面没有是因为如果执行顺利那么会执行self.start_remove()，从而导致这个变异体文件被删除
                checkAndCreateDir(os.path.join(faultlocalizationResultPath, self.project, self.version, "failing_tests"))
                shutil.copy2(os.path.join(self.innerTempSrcPath, "failing_tests"), os.path.join(faultlocalizationResultPath, self.project, self.version, "failing_tests", str(self.muInfo["index"])))

                # region  获取当前执行变异体的执行结果
                with open(os.path.join(self.innerTempSrcPath, "failing_tests"), 'r', encoding='utf-8') as f:
                    lines = f.read()
            else:
                with open(os.path.join(faultlocalizationResultPath, self.project, self.version, "failing_tests", str(self.muInfo["index"])), 'r', encoding='utf-8') as f:
                    lines = f.read()
            lines = lines.split('---')
            lines = [s.strip() for s in lines if s.strip()]
            for s in lines:
                testName = s.split('\n')[0].strip()
                faileTests['type1'].append([testName, s.split('\n')[0]])
                faileTests['type2'].append([testName, s.split('\n')[0] + s.split('\n')[1].split(':')[0]])
                faileTests['type3'].append([testName, s.split('\n')[0] + s.split('\n')[1]])
                faileTests['type4'].append([testName, s])
            # endregion

            # region 获取原始程序的执行结果
            with open(os.path.join(self.faliingTestOutputPath, self.project, self.version, "failing_tests"), 'r', encoding='utf-8') as f:
                lines = f.read()
            lines = lines.split('---')
            lines = [s.strip() for s in lines if s.strip()]
            for s in lines:
                testName = s.split('\n')[0].strip()
                originFaileTests['type1'].append([testName, s.split('\n')[0]])
                originFaileTests['type2'].append([testName, s.split('\n')[0] + s.split('\n')[1].split(':')[0]])
                originFaileTests['type3'].append([testName, s.split('\n')[0] + s.split('\n')[1]])
                originFaileTests['type4'].append([testName, s])
            # endregion

            for t in allTests:
                # passList中，0是通过1是失败 killList中0是存活1是杀死
                for i in range(1, 5):
                    # 四种 MBFL 杀死信息粒度 type1-type4
                    faileTestsList = faileTests[f'type{i}']
                    originFaileTestsList = originFaileTests[f'type{i}']

                    # 当前测试用例是否存在于变异体失败测试用例列表
                    flag_fail = t in [test[0] for test in faileTestsList]
                    # 当前测试用例是否存在于原程序失败测试用例列表
                    flag_origin = t in [test[0] for test in originFaileTestsList]
                    # 区分通过还是失败测试用例是针对原程序的
                    if flag_origin:
                        self.passList.get(f'type{i}').append(1)
                    else:
                        self.passList.get(f'type{i}').append(0)

                    # 获取杀死信息
                    if flag_fail and flag_origin:
                        faileInfo_results = [test for test in faileTestsList if test[0] == t]
                        faileInfo = []
                        for faile_filtered in faileInfo_results:
                            faileInfo.append(faile_filtered[1])

                        originFaileInfo_results = [test for test in originFaileTestsList if test[0] == t]
                        originFaileInfo = []
                        for origin_filtered in originFaileInfo_results:
                            originFaileInfo.append(origin_filtered[1])

                        if faileInfo == originFaileInfo:
                            self.killList.get(f'type{i}').append(0)
                        else:
                            self.killList.get(f'type{i}').append(1)
                            # print(i,' xsq no ',faileInfo,originFaileInfo)
                    elif flag_fail:
                        self.killList.get(f'type{i}').append(1)
                    elif flag_origin:
                        self.killList.get(f'type{i}').append(1)
                    else:
                        self.killList.get(f'type{i}').append(0)
            # # 获取变异体执行结果
            # with open(os.path.join(self.innerTempSrcPath, "failing_tests"), 'r', encoding='utf-8') as f:
            #     lines = f.readlines()
            #     for index, line in enumerate(lines):
            #         if '---' not in line:
            #             continue
            #         testName = line.split('::')[-1].strip()
            #         testInfo = lines[index + 1].strip()
            #         faileTests.append([testName, testInfo])
                    
            # # 获取错误程序失败测试用例信息
            # with open(os.path.join(self.faliingTestOutputPath, self.project, self.version, "failing_tests"), 'r', encoding='utf-8') as f:
            #     lines = f.readlines()
            #     for index, line in enumerate(lines):
            #         if '---' not in line:
            #             continue
            #         testName = line.split('::')[-1].strip()
            #         testInfo = lines[index + 1].strip()
            #         originFaileTests.append([testName, testInfo])
                    
            # # 对比生成杀死矩阵
            # for t in allTests:
            #     # passList中，0是通过1是失败 killList中0是存活1是杀死
            #     if t in list(map(lambda x: x[0],faileTests)):
            #         self.passList.append(1)
            #     else:
            #         self.passList.append(0)
            #     if t in list(map(lambda x: x[0],faileTests)) and t in list(map(lambda x: x[0],originFaileTests)):
            #         # self.mKillList.append(0)
            #         filtered_results = list(filter(lambda x: x[0] == t, faileTests))
            #         if len(filtered_results) > 1:
            #             faileInfo = filtered_results[1]
            #         else:
            #             # 处理没有足够元素的情况
            #             faileInfo = None  # 或者您可以根据需求进行其他处理
            #         filtered_results = list(filter(lambda x: x[0] == t, originFaileTests))
            #         if len(filtered_results) > 1:
            #             originFaileInfo = filtered_results[1]
            #         else:
            #             # 处理没有足够元素的情况
            #             originFaileInfo = None  # 或者您可以根据需求进行其他处理

            #         # faileInfo = filter(lambda x: x[0]==t,faileTests)[1]
            #         # faileInfo = list(filter(lambda x: x[0] == t, faileTests))[1]
            #         # originFaileInfo = filter(lambda x: x[0]==t,originFaileTests)[1]
            #         if faileInfo == originFaileInfo:
            #             self.killList.append(0)
            #         else:
            #             self.killList.append(1)
            #     elif t in list(map(lambda x: x[0],faileTests)):
            #         # self.mKillList.append(1)
            #         self.killList.append(1)
            #     elif t in list(map(lambda x: x[0],originFaileTests)):
            #         # self.mKillList.append(1)
            #         self.killList.append(1)
            #     else:
            #         # self.mKillList.append(0)
            #         self.killList.append(0)
            self.status = 1
        except Exception as e:
            self.status = 0
            exc_type, exc_obj, exc_tb = sys.exc_info()
            line_number = exc_tb.tb_lineno
            file_name = exc_tb.tb_frame.f_code.co_filename
            print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
            return
        # print("-------end compile run-------")

        return

    def start_remove(self):
        # print("-------start remove run-------")
        self.OccupiedVersionMutex.acquire()
        shutil.rmtree(self.innerTempSrcPath)
        self.OccupiedVersionMutex.release()
        # print("-------end remove run-------")
        return


    def start_save(self):
        try:
            # 所有的测试用例
            allTests = []
            # 变异体的失败测试用例
            faileTests = {
                'type1': [],
                'type2': [],
                'type3': [],
                'type4': []
            }
            # 原始程序的失败测试用例
            originFaileTests = {
                'type1': [],
                'type2': [],
                'type3': [],
                'type4': []
            }
            # 获取所有的测试用例
            with open(os.path.join(outputCleanPath, self.project, self.version, "all_tests.txt"), 'r',encoding='utf-8') as f:
                allTests = [line.replace("#","::").strip() for line in f.readlines()]

            # region  获取当前执行变异体的执行结果
            with open(os.path.join(faultlocalizationResultPath, self.project, self.version,"failing_tests/" + str(self.muInfo['index'])), 'r', encoding='utf-8') as f:
                lines = f.read()
            lines = lines.split('---')
            lines = [s.strip() for s in lines if s.strip()]
            for s in lines:
                testName = s.split('\n')[0].strip()
                faileTests['type1'].append([testName, s.split('\n')[0]])
                faileTests['type2'].append([testName, s.split('\n')[0] + s.split('\n')[1].split(':')[0]])
                faileTests['type3'].append([testName, s.split('\n')[0] + s.split('\n')[1]])
                faileTests['type4'].append([testName, s])
            # endregion

            # region 获取原始程序的执行结果
            with open(os.path.join(self.faliingTestOutputPath, self.project, self.version, "failing_tests"), 'r',encoding='utf-8') as f:
                lines = f.read()
            lines = lines.split('---')
            lines = [s.strip() for s in lines if s.strip()]
            for s in lines:
                testName = s.split('\n')[0].strip()
                originFaileTests['type1'].append([testName, s.split('\n')[0]])
                originFaileTests['type2'].append([testName, s.split('\n')[0] + s.split('\n')[1].split(':')[0]])
                originFaileTests['type3'].append([testName, s.split('\n')[0] + s.split('\n')[1]])
                originFaileTests['type4'].append([testName, s])
            # endregion

            for t in allTests:
                # passList中，0是通过1是失败 killList中0是存活1是杀死
                for i in range(1, 5):
                    # 四种 MBFL 杀死信息粒度 type1-type4
                    faileTestsList = faileTests[f'type{i}']
                    originFaileTestsList = originFaileTests[f'type{i}']

                    # 区分通过还是失败测试用例是针对原程序的
                    if t in [test[0] for test in originFaileTestsList]:
                        self.passList.get(f'type{i}').append(1)
                    else:
                        self.passList.get(f'type{i}').append(0)

                    # 获取杀死信息
                    if t in [test[0] for test in faileTestsList] and t in [test[0] for test in originFaileTestsList]:
                        filtered_results = [test for test in faileTestsList if test[0] == t]
                        faileInfo = []
                        for filtered in filtered_results:
                            faileInfo.append(filtered[1])

                        filtered_results = [test for test in originFaileTestsList if test[0] == t]
                        originFaileInfo = []
                        for filtered in filtered_results:
                            originFaileInfo.append(filtered[1])

                        if faileInfo == originFaileInfo:
                            self.killList.get(f'type{i}').append(0)
                        else:
                            self.killList.get(f'type{i}').append(1)
                    elif t in [test[0] for test in faileTestsList]:
                        self.killList.get(f'type{i}').append(1)
                    elif t in [test[0] for test in originFaileTestsList]:
                        self.killList.get(f'type{i}').append(1)
                    else:
                        self.killList.get(f'type{i}').append(0)

            self.status = 1
        except Exception as e:
            self.status = 0
            exc_type, exc_obj, exc_tb = sys.exc_info()
            line_number = exc_tb.tb_lineno
            file_name = exc_tb.tb_frame.f_code.co_filename
            print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
            return
        # print("-------end compile run-------")
        return