import json
import logging
import multiprocessing
import os
import pickle
import sys
import paramiko
import random
import subprocess
from execute.FOM import executeFom, generateFom
from tool.cal_tools import calFomMbfl, countFunctionSus, calSomMbfl, countSOMFunctionSus
from tool.config_variables import (
    SOMfaultlocalizationResultPath,
    djSrcPath,
    faliingTestOutputPath,
    faultlocalizationResultPath,
    mbflMethods,
    mutantsFilePath,
    outputCleanPath,
    password,
    project,
    sbflMethod,
    sourcePath,
    tempSrcPath,
    tpydataPath,
)
from tool.logger_config import logger_config
from tool.other import checkAndCreateDir, clearDir, run
from tool.remote_transmission import cp_from_remote, get_host_ip, ip, sftp_upload
from datetime import datetime


def getSbflSus(project, version):
    """
    获取sbfl的怀疑度值
    :param project: 项目名
    :param version: 版本号
    :return: 错误行信息和怀疑度列表
    suspiciousSbfl存储格式:
    错误文件路径: {
        sbfl方法名:{
            行号: 怀疑度
            ...
            行号: 怀疑度
        }
    }
    faultLocalization存储格式:
    错误文件路径: [行号, ..., 行号]
    }
    """
    try:
        suspiciousSbflPath = os.path.join(
            faultlocalizationResultPath, project, version, "suspiciousSbfl.json"
        )
        faultLocalizationPath = os.path.join(
            faultlocalizationResultPath, project, version, "faultLocalization.json"
        )
        if not os.path.exists(suspiciousSbflPath) or not os.path.exists(
            faultLocalizationPath
        ):
            print("\033[1;32m************** getSbflSus **************\033[0m")
            hugeToFilePath = os.path.join(
                outputCleanPath, project, version, "HugeToFile.txt"
            )
            with open(hugeToFilePath, "r") as f:
                hugeToFileList = f.readlines()
            hugeToFileList = [s.split("\t")[0] for s in hugeToFileList]
            delIndexPath = os.path.join(
                tpydataPath, project, version, "data_saveAgain_del_statement_index"
            )
            with open(delIndexPath, "rb") as f:
                delIndexList = pickle.load(f)
            faultPlusHugePath = os.path.join(
                outputCleanPath, project, version, "faultPlusHuge.in"
            )
            with open(faultPlusHugePath, "rb") as f:
                faultLineDic = pickle.load(f)
            susScorePath = os.path.join(tpydataPath, project, version, "sus_score")
            with open(susScorePath, "rb") as f:
                susScoreList = pickle.load(f)
            faultFilesLine = dict()
            for fault in faultLineDic.keys():
                fileLineNum = list()
                for index in range(0, len(hugeToFileList)):
                    if hugeToFileList[index] in fault:
                        fileLineNum.append(index)
                faultFilesLine[fault] = fileLineNum
            faultSbflSus = dict()
            for num in faultFilesLine.keys():
                # print(num)
                sbflSus = dict()
                for item in sbflMethod:
                    sbflSus[item] = dict()
                    faultSbflSus[num] = dict()
                t = 0
                distance = 0
                tFlag = True
                tFlag2 = True
                for index in range(0, len(hugeToFileList)):
                    if index in faultFilesLine[num] and tFlag:
                        distance = index
                        tFlag = False
                        for i in range(0, len(faultLineDic[num])):
                            faultLineDic[num][i] = faultLineDic[num][i] - distance

                    if delIndexList[index] is False:
                        if index in faultFilesLine[num]:
                            for item in sbflMethod:
                                sbflSus[item][index - distance] = susScoreList[item][t]
                            tFlag2 = False
                        elif tFlag2 is False:
                            break
                        t += 1
                for method in list(sbflSus.keys()):
                    for key in list(sbflSus[method].keys()):
                        if sbflSus[method][key] == 0:
                            del sbflSus[method][key]
                    faultSbflSus[num][method] = dict(
                        sorted(
                            sbflSus[method].items(), key=lambda x: x[1], reverse=True
                        )
                    )
            checkAndCreateDir(os.path.join(faultlocalizationResultPath))
            checkAndCreateDir(os.path.join(faultlocalizationResultPath, project))
            checkAndCreateDir(
                os.path.join(faultlocalizationResultPath, project, version)
            )
            with open(suspiciousSbflPath, "w") as f:
                f.write(json.dumps(faultSbflSus, indent=2))
            with open(faultLocalizationPath, "w") as f:
                f.write(json.dumps(faultLineDic, indent=2))
        with open(suspiciousSbflPath, "r") as f:
            faultSbflSus = json.load(f)
        with open(faultLocalizationPath, "r") as f:
            faultLineDic = json.load(f)
        if ip != "202.4.130.30":
            sftp_upload(
                "202.4.130.30",
                "fanluxi",
                password,
                suspiciousSbflPath,
                suspiciousSbflPath,
            )
        if ip != "202.4.130.30":
            sftp_upload(
                "202.4.130.30",
                "fanluxi",
                password,
                faultLocalizationPath,
                faultLocalizationPath,
            )

        checkAndCreateDir(os.path.join(faultlocalizationResultPath))
        checkAndCreateDir(os.path.join(faultlocalizationResultPath, project))
        checkAndCreateDir(
            os.path.join(faultlocalizationResultPath, project, version)
        )
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")
        return
    print("\033[1;32m************** getSbflSus SUCCESS **************\033[0m")
    return faultLineDic, faultSbflSus


# 一阶变异体
def FOM(project, version, configData):
    # print(project, version)
    logging.info(project + " " + version)
    try:
        faultLineDic, sbflSus = getSbflSus(project, version)
        # print(faultLineDic)
        logging.info(faultLineDic)
        muInfoList = generateFom(project, version)
        resultList = executeFom(project, version, muInfoList, configData)
        calFomMbfl(project, version, muInfoList, resultList)
        countFunctionSus(project, version)
        logging.info(project + " " + version + " success!")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")
        return


if __name__ == "__main__":
    clearDir(tempSrcPath)
    checkAndCreateDir(tempSrcPath)
    logger = logger_config(log_path="logs/main.log")
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    with open("./failVersion.json", "r") as f:
        failVersion = json.load(f)
    with open("./config.json", "r") as configFile:
        configData = json.load(configFile)
    try:
        with multiprocessing.Pool(12) as executor:
            for projectDir in project.keys():
                count = 0
                # projectDir = "Time"
                # projectDir = "Cli"
                # projectDir = "Chart"
                # projectDir = "Closure"
                # projectDir = "Math"
                # projectDir = "Mockito"
                # projectDir = "JacksonDatabind"
                # projectDir = "JxPath"
                for versionNum in range(1, project[projectDir] + 1):
                    versionDir = str(versionNum) + "b"
                    
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    print(formatted_time)
                    executor.apply_async(FOM, (projectDir, versionDir,configData))
                    
            executor.close()
            executor.join()

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")
