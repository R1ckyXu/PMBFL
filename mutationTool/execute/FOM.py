import os
import shutil
import json
import concurrent.futures
import sys
import logging

import execute.FOMExecutorTool as FOMExecutorTool
from tool.config_variables import tempSrcPath, tpydataPath, outputCleanPath, djSrcPath, mutantsFilePath, \
    faliingTestOutputPath, faultlocalizationResultPath, SOMfaultlocalizationResultPath, sbflMethod, sourcePath, \
    password, project
from tool.remote_transmission import ip, get_host_ip, sftp_upload, cp_from_remote
from tool.logger_config import logger_config
from tool.mbfl_formulas import dstar, ochiai, gp13, op2, jaccard, russell, turantula, naish1, binary, crosstab
from tool.other import clearDir, checkAndCreateDir, run


def generateFom(project, version) -> list:
    """
    通过major获取变异体信息
    muInfo存储格式:
    index: 变异体序号
    linenum: 变异体行号
    typeOp: 变异算子类型
    mutFilePath: 变异体存储位置
    relativePath: 变异体文件在项目中的相对路径
    """
    try:
        clearDir("./tmp")
        # 变异体文件存储位置
        mutantPath = os.path.join(mutantsFilePath, project, version)
        if not os.path.exists(mutantPath):
            print('\033[1;32m************** generateFom **************\033[0m')
            shutil.copytree(os.path.join(djSrcPath, project, version), "./tmp")
            run('./tool/runMajor.sh')
            shutil.copytree("./tmp/mutants", mutantPath)
            shutil.copyfile("./tmp/mutants.log", mutantPath + "/mutants.log")
        # 变异体信息存储位置
        muInfoPath = os.path.join(
            faultlocalizationResultPath, project, version, "muInfo.json")
        if not os.path.exists(muInfoPath):
            muInfoList = list()
            with open(mutantPath + "/mutants.log", "r") as f:
                for line in f.readlines():
                    muInfo = dict()
                    muInfo['index'] = int(line.split(':')[0])
                    muInfo['linenum'] = int(line.split(':')[5])
                    muInfo['typeOp'] = line.split(':')[1]
                    muInfoList.append(muInfo)
            for i in os.listdir(mutantPath):
                # 找到以序号为名的文件夹， 除去mutants.log
                if os.path.isdir(os.path.join(mutantPath, i)):
                    mutFileDir = os.listdir(os.path.join(mutantPath, i))[0]
                    mutFilePath = os.path.join(mutantPath, i, mutFileDir)
                    if len(sourcePath[project].keys()) > 1 and int(version[:-1]) > int(
                            list(sourcePath[project].keys())[0]):
                        relativePath = os.path.join(
                            sourcePath[project][list(sourcePath[project].keys())[1]], mutFileDir)
                    else:
                        relativePath = os.path.join(
                            sourcePath[project][list(sourcePath[project].keys())[0]], mutFileDir)
                    # 递归找到文件
                    while os.path.isdir(mutFilePath):
                        mutFileDir = os.listdir(mutFilePath)[0]
                        mutFilePath = os.path.join(mutFilePath, mutFileDir)
                        relativePath += "/" + mutFileDir
                    muInfoList[int(i) - 1]['mutFilePath'] = mutFilePath
                    muInfoList[int(i) - 1]['relativePath'] = relativePath
            with open(muInfoPath, 'w') as f:
                f.write(json.dumps(muInfoList, indent=2))
        with open(muInfoPath, 'r') as f:
            muInfoList = json.load(f)
        if ip != '202.4.130.30':
            sftp_upload('202.4.130.30', 'fanluxi',
                        password, muInfoPath, muInfoPath)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
        return None
    print('\033[1;32m************** generateFom SUCCESS **************\033[0m')
    logging.info(f"xsq nbnbnb" )
    return muInfoList


def execute_fom(muInfo, configData):
    print("变异体编号:", muInfo["index"])
    executor = FOMExecutorTool.Executor(
        muInfo["project"], muInfo["version"], muInfo, configData)
    muExecutResult = {
        "index": muInfo["index"],
        "linenum": muInfo["linenum"],
        "status": executor.status,
        "passList": executor.passList,
        "killList": executor.killList,
        "mKillList": executor.mKillList
    }
    return muExecutResult


def executeFom(project, version, muInfoList, configData):
    """
    执行一阶变异体
    muResult存储格式:
    index: 变异体序号
    linenum: 变异体行号
    status: 执行结果(0为执行失败,1为执行成功)
    passList: 执行结果
    killList: 杀死信息
    mKillList: MUSE版杀死信息
    """
    try:
        muResultPath = os.path.join(
            faultlocalizationResultPath, project, version, "muResult.json")
        if not os.path.exists(muResultPath):  # 应该是 not os.path.exists(muResultPath)
            print('\033[1;32m************** executeFom **************\033[0m')
            resultList = list()
            if muInfoList == None:
                muInfoList = []
            for item in muInfoList:
                item["project"] = project
                item["version"] = version
            # 创建线程池 正常max_workers=3
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                future_results = [executor.submit(execute_fom, muInfo, configData) for muInfo in muInfoList]

                for future_result in future_results:
                    try:
                        result = future_result.result(5 * 60)
                        resultList.append(result)
                    except concurrent.futures.TimeoutError:
                        print("Task timed out and will be terminated")
                        # executor.shutdown(wait=False)#????????  超时所有测试用例都记为杀死or仅超时测试用例记为杀死
                        # break#????????                   超时就把这个变异体丢掉
                    except KeyboardInterrupt:
                        print("Interrupted by user and will be terminated")
                        executor.shutdown(wait=False)
                        exit(1)
            with open(muResultPath, 'w') as f:
                f.write(json.dumps(resultList, indent=2))
        with open(muResultPath, 'r') as f:
            resultList = json.load(f)
        if ip != '202.4.130.30':
            sftp_upload('202.4.130.30', 'fanluxi', password, muResultPath, muResultPath)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
        logging.error(f'Error in {file_name} at line {line_number}: {e}')
        return
    print('\033[1;32m************** executeFom SUCCESS **************\033[0m')
    return resultList
