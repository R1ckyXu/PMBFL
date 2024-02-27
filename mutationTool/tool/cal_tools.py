import json
import logging
import math
import operator
import os
import pickle
import sys
import shutil
from collections import defaultdict
from execute.FOM import executeFom, generateFom
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
    method_names,
)
from tool.logger_config import logger_config
from tool.mbfl_formulas import (
    binary,
    crosstab,
    dstar,
    gp13,
    jaccard,
    naish1,
    ochiai,
    op2,
    russell,
    turantula,
)
from tool.other import checkAndCreateDir, clearDir, run
from tool.remote_transmission import cp_from_remote, get_host_ip, ip, sftp_upload

def countTotal(directory):
    output_file = os.path.join(directory, 'total.json')
    if os.path.exists(output_file):
        # 删除文件
        os.remove(output_file)
    merged_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)
                for key, sub_dict in data.items():
                    for sub_key, value in sub_dict.items():
                        for key1, value1 in value.items():
                            merged_data[key][sub_key][key1] += value1
    with open(output_file, 'w') as f:
        f.write(json.dumps(merged_data, indent=2))

def countTotalMARandMFR(directory):
    output_file = os.path.join(directory, 'total.json')
    if os.path.exists(output_file):
        # 删除文件
        os.remove(output_file)
    # 初始化一个空字典来存储所有数据
    total_data = {}

    # 初始化一个字典来存储每个指标的总和
    sum_data = {}

    # 初始化一个字典来存储每个指标出现的次数
    count_data = {}

    # 遍历目录下的所有文件
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        with open(file_path, "r") as f:
            # 读取 JSON 文件内容
            file_data = json.load(f)
            
            # 更新指标总和和计数
            for indicator, values in file_data.items():
                if indicator not in sum_data:
                    sum_data[indicator] = {}
                    count_data[indicator] = {}
                for key, value in values.items():
                    if key not in sum_data[indicator]:
                        sum_data[indicator][key] = 0
                        count_data[indicator][key] = 0
                    sum_data[indicator][key] += value
                    count_data[indicator][key] += 1

    # 计算平均值
    for indicator, values in sum_data.items():
        if indicator not in total_data:
            total_data[indicator] = {}
        for key, value in values.items():
            total_data[indicator][key] = value / count_data[indicator][key]

    with open(output_file, "w") as f:
        json.dump(total_data, f, indent=4)  # 缩进为4个空格，可选

def calSbfl(project, version):
    try:
        if os.path.exists(
            faultlocalizationResultPath
            + "/"
            + project
            + "/"
            + version
            + "/susStatement/sbfl.json"
        ):
            with open(
                faultlocalizationResultPath
                + "/"
                + project
                + "/"
                + version
                + "/susStatement/sbfl.json",
                "r",
            ) as f:
                susResult = json.load(f)
        else:
            sus1 = dict()
            susResult = dict()
            with open(
                faultlocalizationResultPath
                + "/"
                + project
                + "/"
                + version
                + "/suspiciousSbfl.json",
                "r",
            ) as f:
                sus1 = json.load(f)

            for key in sus1.keys():
                for key1 in sus1[key].keys():
                    if key1 in method_names:
                        if susResult.get(key[1:]) == None:
                            susResult[key[1:]] = dict()
                        susResult[key[1:]][key1] = sus1[key][key1]
            # print(os.path.dirname(resultPath))
            checkAndCreateDir(
                os.path.dirname(
                    faultlocalizationResultPath
                    + "/"
                    + project
                    + "/"
                    + version
                    + "/susStatement/"
                )
            )
            with open(
                faultlocalizationResultPath
                + "/"
                + project
                + "/"
                + version
                + "/susStatement/sbfl.json",
                "w",
            ) as f:
                f.write(json.dumps(susResult, indent=2))
        #  临时注释
        # if os.path.exists(faultlocalizationResultPath + "/" + project + "/" + version + "/susFunction/sbfl.json"):
        #     with open(faultlocalizationResultPath + "/" + project + "/" + version + "/susFunction/sbfl.json", 'r') as f:
        #         functionSus = json.load(f)
        # else:
        if True:
            with open(
                "../../d4j/hugeToFunction/"
                + project
                + "/"
                + version
                + "/HugetoFunction.in",
                "rb",
            ) as f:
                hugeToFunction = pickle.load(f)
            with open(
                outputCleanPath + "/" + project + "/" + version + "/faultHuge_Function.in",
                "rb",
            ) as f:
                faultHuge_Function = pickle.load(f)
            with open(
                outputCleanPath + "/" + project + "/" + version + "/FunctionList.txt", "r"
            ) as f:
                FunctionList = f.readlines()
            with open(
                outputCleanPath + "/" + project + "/" + version + "/HugeToFile.txt", "r"
            ) as f:
                hugeToFile = f.readlines()
            with open(
                outputCleanPath
                + "/"
                + project
                + "/"
                + version
                + "/CoverageMatrix_Function.in",
                "rb",
            ) as f:
                CoverageMatrix_Function = pickle.load(f)
            with open(
                outputCleanPath + "/" + project + "/" + version + "/inVector.txt", "r"
            ) as f:
                inVector = f.readlines()

            hugeToFiledict = dict()
            for i in range(0, len(hugeToFile)):
                if hugeToFiledict.get(hugeToFile[i].split("\t")[0]) == None:
                    hugeToFiledict[hugeToFile[i].split("\t")[0]] = dict()
                functionLine = hugeToFunction[i] + 1
                    
                count = sum(
                    1
                    for element in FunctionList[0:functionLine]
                    if FunctionList[functionLine - 1].split(":")[0] in element
                )
                hugeToFiledict[hugeToFile[i].split("\t")[0]][
                    hugeToFile[i].split("\t")[1].strip()
                ] = count
            checkAndCreateDir(
                faultlocalizationResultPath + "/" + project + "/" + version + "/susFunction"
            )

            # 应该使用方法级的覆盖信息
            # 1.首先找到错误的.java下的所有函数的起止位置 2.计算.java下的所有sbfl怀疑度 3.存到/susFunction/sbfl.json
            # flx version
            # functionSus = {}
            # for key in susResult.keys():
            #     functionSus[key] = dict()
            #     for method in susResult[key].keys():
            #         functionSus[key][method] = dict()
            #         for line in susResult[key][method].keys():
            #             for k in hugeToFiledict.keys():
            #                 if k in key:
            #                     break
            #             if hugeToFiledict[k].get(str(int(line)-1)) == None:
            #                 continue
            #             count = hugeToFiledict[k][str(int(line)-1)]
            #             if functionSus[key][method].get(count)==None:
            #                 functionSus[key][method][count] = susResult[key][method][line]

            functionSus = {}
            for key in susResult.keys():
                # region 1.首先找到错误的.java下的所有函数的起止位置
                beginLine = -1
                endLine = -1
                cnt = 0
                findFlag = -1
                for line in FunctionList:
                    if line.split(":")[0] in key:
                        if beginLine == -1:
                            beginLine = cnt
                        endLine = cnt
                    if findFlag == 0 and line.split(":")[0] not in key:
                        break
                    cnt = cnt + 1
                cnt = endLine - beginLine + 1
                # endregion

                # region 2.收集每个函数的覆盖信息
                covInfo = list()
                # 遍历所有函数
                for cov_i in range(beginLine, endLine + 1):
                    ef = 0
                    nf = 0
                    ep = 0
                    np = 0
                    # 遍历所有测试用例
                    for cov_j in range(len(CoverageMatrix_Function)):
                        # 失败测试用例
                        if inVector[cov_j].strip() == "1":
                            if CoverageMatrix_Function[cov_j][cov_i] == 1:
                                ef = ef + 1
                            else:
                                nf = nf + 1
                        # 通过测试用例
                        else:
                            if CoverageMatrix_Function[cov_j][cov_i] == 1:
                                ep = ep + 1
                            else:
                                np = np + 1

                    item = dict()
                    item["ef"] = ef
                    item["nf"] = nf
                    item["ep"] = ep
                    item["np"] = np
                    covInfo.append(item)
                # endregion

                # region 3.计算每个函数每个方法的怀疑度
                functionSus[key] = dict()
                for method in mbflMethods:
                    method_name = method.__name__
                    if functionSus[key].get(method_name) == None:
                        functionSus[key][method_name] = dict()
                    for index in range(len(covInfo)):
                        ef = covInfo[index]["ef"]
                        nf = covInfo[index]["nf"]
                        ep = covInfo[index]["ep"]
                        np = covInfo[index]["np"]
                        functionSus[key][method_name][str(index + 1)] = method(
                            ef, nf, ep, np
                        )
                    method_dict = functionSus[key][method_name]
                    functionSus[key][method_name] = dict(
                        sorted(method_dict.items(), key=lambda x: x[1], reverse=True)
                    )
                # endregion

            with open(
                faultlocalizationResultPath
                + "/"
                + project
                + "/"
                + version
                + "/susFunction/sbfl.json",
                "w",
            ) as f:
                f.write(json.dumps(functionSus, indent=2))
        return susResult, functionSus
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")


def calFomMbfl(project, version, muInfoList, resultList):
    """
    通过变异体的执行矩阵和杀死矩阵计算语句怀疑度
    :param Fom: 变异体的信息,主要用到行号
    :param FomResult: 变异体的执行结果和杀死信息,数组形式存储,第一个是执行结果,第二个是杀死信息.
                      执行结果: 1代表失败,0代表通过
                      杀死信息: 1代表杀死,0代表没杀死
    :return: 变异体信息列表
    """
    try:
        suspiciousFirstOrderPath = os.path.join(
            faultlocalizationResultPath,
            project,
            version,
            "susStatement",
            "complete.json",
        )
        susResult = {}
        susFOM = {}
        susFOMPath = os.path.join(
            faultlocalizationResultPath, project, version, "susFOM.json"
        )
        for j in range(1, 5):
            susResult[f"type{j}"] = dict()
            susFOM[f"type{j}"] = dict()
            for method in mbflMethods:
                susFOM[f"type{j}"][str(method).split(" ")[1]] = list()
            if resultList == None:
                resultList = []
            for i in range(0, len(resultList)):
                if resultList[i]["status"] == 0:
                    susFOM[f"type{j}"][str(method).split(" ")[1]].append(0)
                    continue
                Anp = 0
                Anf = 0
                Akp = 0
                Akf = 0
                if susResult[f"type{j}"].get(muInfoList[i]["relativePath"]) == None:
                    susResult[f"type{j}"][muInfoList[i]["relativePath"]] = dict()
                for index in range(0, len(resultList[i]["passList"][f"type{j}"])):
                    if resultList[i]["passList"][f"type{j}"][index] == 1:
                        if resultList[i]["killList"][f"type{j}"][index] == 1:
                            Akf += 1
                        else:
                            Anf += 1
                    else:
                        if resultList[i]["killList"][f"type{j}"][index] == 1:
                            Akp += 1
                        else:
                            Anp += 1
                for method in mbflMethods:
                    susFOM[f"type{j}"][str(method).split(" ")[1]].append(
                        method(Akf, Anf, Akp, Anp)
                    )
                    if (
                        susResult[f"type{j}"][muInfoList[i]["relativePath"]].get(
                            str(method).split(" ")[1]
                        )
                        == None
                    ):
                        susResult[f"type{j}"][muInfoList[i]["relativePath"]][
                            str(method).split(" ")[1]
                        ] = dict()
                    if (
                        susResult[f"type{j}"][muInfoList[i]["relativePath"]][
                            str(method).split(" ")[1]
                        ].get(resultList[i]["linenum"])
                        == None
                    ):
                        susResult[f"type{j}"][muInfoList[i]["relativePath"]][
                            str(method).split(" ")[1]
                        ][resultList[i]["linenum"]] = method(Akf, Anf, Akp, Anp)
                    else:
                        susResult[f"type{j}"][muInfoList[i]["relativePath"]][
                            str(method).split(" ")[1]
                        ][resultList[i]["linenum"]] = max(
                            susResult[f"type{j}"][muInfoList[i]["relativePath"]][
                                str(method).split(" ")[1]
                            ][resultList[i]["linenum"]],
                            method(Akf, Anf, Akp, Anp),
                        )
                for item in susResult[f"type{j}"].keys():
                    for method in mbflMethods:
                        susResult[f"type{j}"][item][str(method).split(" ")[1]] = dict(
                            sorted(
                                susResult[f"type{j}"][item][
                                    str(method).split(" ")[1]
                                ].items(),
                                key=operator.itemgetter(1),
                                reverse=True,
                            )
                        )

        checkAndCreateDir(os.path.join(faultlocalizationResultPath, project))
        checkAndCreateDir(os.path.join(faultlocalizationResultPath, project, version))
        checkAndCreateDir(
            os.path.join(faultlocalizationResultPath, project, version, "susStatement")
        )
        with open(suspiciousFirstOrderPath, "w") as f:
            f.write(json.dumps(susResult, indent=2))
        with open(susFOMPath, "w") as f:
            f.write(json.dumps(susFOM, indent=2))
        if ip != "202.4.130.30":
            sftp_upload(
                "202.4.130.30",
                "fanluxi",
                password,
                suspiciousFirstOrderPath,
                suspiciousFirstOrderPath,
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")


# 计算MFR MAR
def calMFRandMAR(project, version, topNResult, FileName, mode):
    try:
        MFR = dict()
        MAR = dict()
        cnt = 0
        for key in topNResult.keys():
            for line in topNResult[key].keys():
                cnt = cnt + 1
                for method, value in topNResult[key][line].items():
                    # 统计MFR
                    if MFR.get(method) is None:
                        MFR[method] = value
                    if MFR[method] > value:
                        MFR[method] = value
                    # 统计MAR
                    if MAR.get(method) is None:
                        MAR[method] = 0
                    MAR[method] += value
        for method in MAR.keys():
            MAR[method] = MAR[method] / cnt

        checkAndCreateDir(os.path.join(faultlocalizationResultPath, project, version, f"{mode}_MFR"))
        checkAndCreateDir(os.path.join(faultlocalizationResultPath, project, version, f"{mode}_MAR"))
        with open(os.path.join(faultlocalizationResultPath, project, version, f"{mode}_MFR", FileName), 'w') as f:
            f.write(json.dumps(MFR, indent=2))
            f.close()
        with open(os.path.join(faultlocalizationResultPath, project, version, f"{mode}_MAR", FileName), 'w') as f:
            f.write(json.dumps(MAR, indent=2))
            f.close()

        return MFR, MAR
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        print(f'\033[1;31mError at line {line_number}: {e}\033[0m')
        logging.error(f'Error at line {line_number}: {e}')


def calTopNMbfl(project, version, susResult, FileName, mode):
    try:
        topNResultBest = dict()
        topNResultAverage = dict()
        topNResultWorst = dict()
        with open(
            os.path.join(
                faultlocalizationResultPath, project, version, "falutFunction.json"
            ),
            "r",
        ) as f:
            faultLocalization = json.load(f)
        # 将真实错误函数信息拼接起来
        faultFunc = list()
        tmp = "<419>"
        for item in faultLocalization:
            for index in faultLocalization[item]:
                faultFunc.append(item[1:] + tmp + str(index))

        for method in mbflMethods:
            method_name = method.__name__
            # 将同一公式下的所有函数进行统一排序生成newSusResult
            newSusResult = dict()
            if FileName == "sbfl.json":
                for item in susResult:
                    # print(susResult.keys())
                    for suskey, value in susResult[item][method_name].items():
                        k = item + tmp + str(suskey)
                        newSusResult[k] = value
                newSusResult = dict(
                    sorted(newSusResult.items(), key=lambda item: item[1], reverse=True)
                )
            elif "czx" in FileName:
                for item in susResult["type3"]:
                    # print(susResult.keys())
                    for suskey, value in susResult["type3"][item][method_name].items():
                        k = item + tmp + str(suskey)
                        newSusResult[k] = value
                newSusResult = dict(
                    sorted(newSusResult.items(), key=lambda item: item[1], reverse=True)
                )
                

            else:
                for item in susResult["type3"]:
                    # print(susResult.keys())
                    for suskey, value in susResult["type3"][item][method_name].items():
                        k = item + tmp + str(suskey)
                        newSusResult[k] = value
                newSusResult = dict(
                    sorted(newSusResult.items(), key=lambda item: item[1], reverse=True)
                )

            for faultKey in faultFunc:
                key = "/" + faultKey.split("<419>")[0]
                line = faultKey.split("<419>")[1]
                # region 创建字典
                if topNResultBest.get(key) is None:
                    topNResultBest[key] = dict()
                if topNResultBest[key].get(line) is None:
                    topNResultBest[key][line] = dict()
                if topNResultAverage.get(key) is None:
                    topNResultAverage[key] = dict()
                if topNResultAverage[key].get(line) is None:
                    topNResultAverage[key][line] = dict()
                if topNResultWorst.get(key) is None:
                    topNResultWorst[key] = dict()
                if topNResultWorst[key].get(line) is None:
                    topNResultWorst[key][line] = dict()
                # endregion

                if newSusResult.get(faultKey) is None:
                    topNResultBest[key][line][method_name] = -1
                    topNResultAverage[key][line][method_name] = -1
                    topNResultWorst[key][line][method_name] = -1
                    continue

                faultSus = newSusResult[faultKey]

                startFlagIndex = -1
                repeatFaultTime = 0
                endFlagIndex = -1
                ind = 0
                for item, value in newSusResult.items():
                    # print(value, faultSus)
                    ind += 1
                    if math.isnan(value):
                        continue
                    if value > faultSus:
                        continue
                    if value == faultSus:
                        if startFlagIndex == -1:
                            startFlagIndex = ind
                        else:
                            if item in faultFunc:
                                # repeatFaultTime += 1
                                repeatFaultTime += 0
                    else:
                        endFlagIndex = ind - 1 - repeatFaultTime
                        # print(ind, repeatFaultTime)
                        break
                # 最好排名
                topNResultBest[key][line][method_name] = startFlagIndex
                # 平均排名
                if endFlagIndex == -1:
                    endFlagIndex = ind
                if startFlagIndex == -1 or endFlagIndex == -1:
                    topNResultAverage[key][line][method_name] = -1
                else:
                    topNResultAverage[key][line][method_name] = (
                        startFlagIndex + endFlagIndex
                    ) / 2
                # print(endFlagIndex)
                # 最坏排名
                topNResultWorst[key][line][method_name] = endFlagIndex

        checkAndCreateDir(
            os.path.join(
                faultlocalizationResultPath, project, version, f"TopN{mode}Best"
            )
        )
        checkAndCreateDir(
            os.path.join(
                faultlocalizationResultPath, project, version, f"TopN{mode}Average"
            )
        )
        checkAndCreateDir(
            os.path.join(
                faultlocalizationResultPath, project, version, f"TopN{mode}Worst"
            )
        )
        with open(
            os.path.join(
                faultlocalizationResultPath,
                project,
                version,
                f"TopN{mode}Best",
                FileName,
            ),
            "w",
        ) as f:
            f.write(json.dumps(topNResultBest, indent=2))
            f.close()
        with open(
            os.path.join(
                faultlocalizationResultPath,
                project,
                version,
                f"TopN{mode}Average",
                FileName,
            ),
            "w",
        ) as f:
            f.write(json.dumps(topNResultAverage, indent=2))
            f.close()
        with open(
            os.path.join(
                faultlocalizationResultPath,
                project,
                version,
                f"TopN{mode}Worst",
                FileName,
            ),
            "w",
        ) as f:
            f.write(json.dumps(topNResultWorst, indent=2))
            f.close()

        return topNResultBest, topNResultAverage, topNResultWorst
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        print(f"\033[1;31mError at line {line_number}: {e}\033[0m")
        logging.error(f"Error at line {line_number}: {e}")

def countFunctionSus(project, version):
    try:
        with open("../../d4j/hugeToFunction/" + project + "/" + version + "/HugetoFunction.in", 'rb') as f:
            hugeToFunction = pickle.load(f)
        with open("../../d4j/outputClean/" + project + "/" + version + "/faultHuge_Function.in", 'rb') as f:
            faultHuge_Function = pickle.load(f)
        with open("../../d4j/outputClean/" + project + "/" + version + "/FunctionList.txt", 'r') as f:
            FunctionList = f.readlines()
        with open("../../d4j/outputClean/" + project + "/" + version + "/HugeToFile.txt", 'r') as f:
            hugeToFile = f.readlines()
        # region 生成 falutFunction.json
        falutFunction = dict()
        for key in faultHuge_Function.keys():
            falutFunction[key] = list()
            for line in faultHuge_Function[key]:
                # XSQ
                count = sum(1 for element in FunctionList[0:line] if FunctionList[line].split(":")[0] in element) + 1
                # fanluxi
                # count = sum(1 for element in FunctionList[0:line] if FunctionList[line-1].split(":")[0] in element) + 1
                if count not in falutFunction[key]:
                    falutFunction[key].append(count)
        with open(faultlocalizationResultPath + "/" + project + "/" + version + "/falutFunction.json", 'w') as f:
            f.write(json.dumps(falutFunction, indent=2))
        # endregion

        hugeToFiledict = dict()
        for i in range(0, len(hugeToFile)):
            if hugeToFiledict.get(hugeToFile[i].split("\t")[0]) == None:
                hugeToFiledict[hugeToFile[i].split("\t")[0]] = dict()
            functionLine = hugeToFunction[i] + 1
            count = sum(1 for element in FunctionList[0:functionLine] if
                        FunctionList[functionLine - 1].split(":")[0] in element)
            hugeToFiledict[hugeToFile[i].split("\t")[0]][hugeToFile[i].split("\t")[1].strip()] = count

        suspiciousPath = faultlocalizationResultPath + "/" + project + "/" + version + "/susStatement"
        for root, dirs, files in os.walk(suspiciousPath):
            for file in files:
                checkAndCreateDir(faultlocalizationResultPath + "/" + project + "/" + version + "/susFunction")
                functionSus = dict()
                file_path = os.path.join(root, file)
                # if os.path.exists(faultlocalizationResultPath + "/" + project + "/" + version + "/susFunction/" + file):
                #     continue
                if file == 'sbfl.json':
                    continue
                print(file_path)
                with open(file_path, 'r') as f:
                    sus = json.load(f)
                for j in range(1, 5):
                    functionSus[f'type{j}'] = dict()
                    for key in sus[f'type{j}'].keys():
                        functionSus[f'type{j}'][key] = dict()
                        for method in sus[f'type{j}'][key].keys():
                            functionSus[f'type{j}'][key][method] = dict()
                            for line in sus[f'type{j}'][key][method].keys():
                                for k in hugeToFiledict.keys():
                                    if k in key:
                                        break
                                if hugeToFiledict[k].get(str(int(line) - 1)) == None:
                                    continue
                                count = hugeToFiledict[k][str(int(line) - 1)]
                                if functionSus[f'type{j}'][key][method].get(count) == None:
                                    functionSus[f'type{j}'][key][method][count] = sus[f'type{j}'][key][method][line]
                with open(faultlocalizationResultPath + "/" + project + "/" + version + "/susFunction/" + file,
                          'w') as f:
                    f.write(json.dumps(functionSus, indent=2))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f'\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m')
        logging.error(f'Error in {file_name} at line {line_number}: {e}')


def calTopNMbflAverage(project, version, susResult, FileName, FaultFile, dir):
    try:
        topNResult = dict()
        with open(
            os.path.join(faultlocalizationResultPath, project, version, FaultFile), "r"
        ) as f:
            faultLocalization = json.load(f)
        if FileName == "sbfl.json":
            for key in faultLocalization.keys():
                topNResult[key] = dict()
                for line in faultLocalization[key]:
                    topNResult[key][line] = dict()
                    f = key[1:]
                    if susResult.get(f) is None:
                        for method in mbflMethods:
                            topNResult[key][line][str(method).split(" ")[1]] = -1
                        continue
                    for method in susResult[f].keys():
                        susOfFaultStatement = {}
                        for i in range(len(faultLocalization[key])):
                            if (
                                susResult[f][method].get(str(faultLocalization[key][i]))
                                == None
                            ):
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = -math.inf
                            else:
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = susResult[f][method][str(faultLocalization[key][i])]
                        startFlagIndex = -1
                        repeatFaultTime = 0
                        endFlagIndex = -1
                        ind = 0
                        for item, value in susResult[f][method].items():
                            ind += 1
                            if math.isnan(value):
                                continue
                            if value > susOfFaultStatement[line]:
                                continue
                            if value == susOfFaultStatement[line]:
                                if startFlagIndex == -1:
                                    startFlagIndex = ind
                                else:
                                    if int(item) in faultLocalization[key]:
                                        repeatFaultTime += 1
                            else:
                                endFlagIndex = ind - 1 - repeatFaultTime
                                break
                        if endFlagIndex == -1:
                            endFlagIndex = ind
                        if startFlagIndex == -1 or endFlagIndex == -1:
                            topNResult[key][line][method] = -1
                        else:
                            topNResult[key][line][method] = (
                                startFlagIndex + endFlagIndex
                            ) / 2
            checkAndCreateDir(
                os.path.join(faultlocalizationResultPath, project, version, dir)
            )
            with open(
                os.path.join(
                    faultlocalizationResultPath, project, version, dir, FileName
                ),
                "w",
            ) as f:
                f.write(json.dumps(topNResult, indent=2))
            return topNResult
        for j in range(1, 5):
            topNResult[f"type{j}"] = dict()
            for key in faultLocalization.keys():
                topNResult[f"type{j}"][key] = dict()
                for line in faultLocalization[key]:
                    topNResult[f"type{j}"][key][line] = dict()
                    f = key[1:]
                    if susResult[f"type{j}"].get(f) is None:
                        for method in mbflMethods:
                            topNResult[f"type{j}"][key][line][
                                str(method).split(" ")[1]
                            ] = -1
                        continue
                    for method in susResult[f"type{j}"][f].keys():
                        susOfFaultStatement = {}
                        for i in range(len(faultLocalization[key])):
                            if (
                                susResult[f"type{j}"][f][method].get(
                                    str(faultLocalization[key][i])
                                )
                                == None
                            ):
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = -math.inf
                            else:
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = susResult[f"type{j}"][f][method][
                                    str(faultLocalization[key][i])
                                ]
                        startFlagIndex = -1
                        repeatFaultTime = 0
                        endFlagIndex = -1
                        ind = 0
                        for item, value in susResult[f"type{j}"][f][method].items():
                            ind += 1
                            if math.isnan(value):
                                continue
                            if value > susOfFaultStatement[line]:
                                continue
                            if value == susOfFaultStatement[line]:
                                if startFlagIndex == -1:
                                    startFlagIndex = ind
                                else:
                                    if int(item) in faultLocalization[key]:
                                        repeatFaultTime += 1
                            else:
                                endFlagIndex = ind - 1 - repeatFaultTime
                                break
                        if endFlagIndex == -1:
                            endFlagIndex = ind
                        if startFlagIndex == -1 or endFlagIndex == -1:
                            topNResult[f"type{j}"][key][line][method] = -1
                        else:
                            topNResult[f"type{j}"][key][line][method] = (
                                startFlagIndex + endFlagIndex
                            ) / 2
        checkAndCreateDir(
            os.path.join(faultlocalizationResultPath, project, version, dir)
        )
        with open(
            os.path.join(faultlocalizationResultPath, project, version, dir, FileName),
            "w",
        ) as f:
            f.write(json.dumps(topNResult, indent=2))
        return topNResult
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")


def calTopNMbflBest(project, version, susResult, FileName, FaultFile, dir):
    try:
        topNResult = dict()
        with open(
            os.path.join(faultlocalizationResultPath, project, version, FaultFile), "r"
        ) as f:
            faultLocalization = json.load(f)
        if FileName == "sbfl.json":
            for key in faultLocalization.keys():  # 遍历所有错误文件
                topNResult[key] = dict()
                for line in faultLocalization[key]:  # 遍历所有错误行
                    topNResult[key][line] = dict()
                    f = key[1:]
                    if susResult.get(f) is None:
                        for method in mbflMethods:
                            topNResult[key][line][str(method).split(" ")[1]] = -1
                        continue
                    for method in susResult[f].keys():
                        susOfFaultStatement = {}
                        for i in range(len(faultLocalization[key])):  # 拿到错误语句的怀疑度分数
                            if (
                                susResult[f][method].get(str(faultLocalization[key][i]))
                                == None
                            ):
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = -math.inf
                            else:
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = susResult[f][method][str(faultLocalization[key][i])]
                        startFlagIndex = -1
                        repeatFaultTime = 0
                        endFlagIndex = -1
                        ind = 0
                        for item, value in susResult[f][method].items():
                            ind += 1
                            if math.isnan(value):
                                continue
                            if value > susOfFaultStatement[line]:
                                continue
                            if value == susOfFaultStatement[line]:
                                if startFlagIndex == -1:
                                    startFlagIndex = ind
                                else:
                                    if int(item) in faultLocalization[key]:
                                        repeatFaultTime += 1
                            else:
                                endFlagIndex = ind - 1 - repeatFaultTime
                                break
                        topNResult[key][line][method] = startFlagIndex
            checkAndCreateDir(
                os.path.join(faultlocalizationResultPath, project, version, dir)
            )
            with open(
                os.path.join(
                    faultlocalizationResultPath, project, version, dir, FileName
                ),
                "w",
            ) as f:
                f.write(json.dumps(topNResult, indent=2))
            return topNResult
        for j in range(1, 5):  # 为什么没有else
            topNResult[f"type{j}"] = dict()
            for key in faultLocalization.keys():
                topNResult[f"type{j}"][key] = dict()
                for line in faultLocalization[key]:
                    topNResult[f"type{j}"][key][line] = dict()
                    f = key[1:]
                    if susResult[f"type{j}"].get(f) is None:
                        for method in mbflMethods:
                            topNResult[f"type{j}"][key][line][
                                str(method).split(" ")[1]
                            ] = -1
                        continue
                    for method in susResult[f"type{j}"][f].keys():
                        susOfFaultStatement = {}
                        for i in range(len(faultLocalization[key])):
                            if (
                                susResult[f"type{j}"][f][method].get(
                                    str(faultLocalization[key][i])
                                )
                                == None
                            ):
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = -math.inf
                            else:
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = susResult[f"type{j}"][f][method][
                                    str(faultLocalization[key][i])
                                ]
                        startFlagIndex = -1
                        repeatFaultTime = 0
                        endFlagIndex = -1
                        ind = 0
                        for item, value in susResult[f"type{j}"][f][method].items():
                            ind += 1
                            if math.isnan(value):
                                continue
                            if value > susOfFaultStatement[line]:
                                continue
                            if value == susOfFaultStatement[line]:
                                if startFlagIndex == -1:
                                    startFlagIndex = ind
                                else:
                                    if int(item) in faultLocalization[key]:
                                        repeatFaultTime += 1
                            else:
                                endFlagIndex = ind - 1 - repeatFaultTime
                                break

                        topNResult[f"type{j}"][key][line][method] = startFlagIndex

        checkAndCreateDir(
            os.path.join(faultlocalizationResultPath, project, version, dir)
        )
        with open(
            os.path.join(faultlocalizationResultPath, project, version, dir, FileName),
            "w",
        ) as f:
            f.write(json.dumps(topNResult, indent=2))
        return topNResult
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")


def calTopNMbflWorst(project, version, susResult, FileName, FaultFile, dir):
    try:
        topNResult = dict()
        with open(
            os.path.join(faultlocalizationResultPath, project, version, FaultFile), "r"
        ) as f:
            faultLocalization = json.load(f)

        if FileName == "sbfl.json":
            for key in faultLocalization.keys():
                topNResult[key] = dict()
                for line in faultLocalization[key]:
                    topNResult[key][line] = dict()
                    f = key[1:]
                    if susResult.get(f) is None:
                        for method in mbflMethods:
                            topNResult[key][line][str(method).split(" ")[1]] = -1
                        continue
                    for method in susResult[f].keys():
                        susOfFaultStatement = {}
                        for i in range(len(faultLocalization[key])):
                            if (
                                susResult[f][method].get(str(faultLocalization[key][i]))
                                == None
                            ):
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = -math.inf
                            else:
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = susResult[f][method][str(faultLocalization[key][i])]
                        startFlagIndex = -1
                        repeatFaultTime = 0
                        endFlagIndex = -1
                        ind = 0
                        for item, value in susResult[f][method].items():
                            ind += 1
                            if math.isnan(value):
                                continue
                            if value > susOfFaultStatement[line]:
                                continue
                            if value == susOfFaultStatement[line]:
                                if startFlagIndex == -1:
                                    startFlagIndex = ind
                                else:
                                    if int(item) in faultLocalization[key]:
                                        repeatFaultTime += 1
                            else:
                                endFlagIndex = ind - 1 - repeatFaultTime
                                break
                        topNResult[key][line][method] = endFlagIndex
            checkAndCreateDir(
                os.path.join(faultlocalizationResultPath, project, version, dir)
            )
            with open(
                os.path.join(
                    faultlocalizationResultPath, project, version, dir, FileName
                ),
                "w",
            ) as f:
                f.write(json.dumps(topNResult, indent=2))
            return topNResult
        for j in range(1, 5):
            topNResult[f"type{j}"] = dict()
            for key in faultLocalization.keys():
                topNResult[f"type{j}"][key] = dict()
                for line in faultLocalization[key]:
                    topNResult[f"type{j}"][key][line] = dict()
                    f = key[1:]
                    if susResult[f"type{j}"].get(f) is None:
                        for method in mbflMethods:
                            topNResult[f"type{j}"][key][line][
                                str(method).split(" ")[1]
                            ] = -1
                        continue
                    for method in susResult[f"type{j}"][f].keys():
                        susOfFaultStatement = {}
                        for i in range(len(faultLocalization[key])):
                            if (
                                susResult[f"type{j}"][f][method].get(
                                    str(faultLocalization[key][i])
                                )
                                == None
                            ):
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = -math.inf
                            else:
                                susOfFaultStatement[
                                    faultLocalization[key][i]
                                ] = susResult[f"type{j}"][f][method][
                                    str(faultLocalization[key][i])
                                ]
                        startFlagIndex = -1
                        repeatFaultTime = 0
                        endFlagIndex = -1
                        ind = 0
                        for item, value in susResult[f"type{j}"][f][method].items():
                            ind += 1
                            if math.isnan(value):
                                continue
                            if value > susOfFaultStatement[line]:
                                continue
                            if value == susOfFaultStatement[line]:
                                if startFlagIndex == -1:
                                    startFlagIndex = ind
                                else:
                                    if int(item) in faultLocalization[key]:
                                        repeatFaultTime += 1
                            else:
                                endFlagIndex = ind - 1 - repeatFaultTime
                                break

                        topNResult[f"type{j}"][key][line][method] = endFlagIndex

        checkAndCreateDir(
            os.path.join(faultlocalizationResultPath, project, version, dir)
        )
        with open(
            os.path.join(faultlocalizationResultPath, project, version, dir, FileName),
            "w",
        ) as f:
            f.write(json.dumps(topNResult, indent=2))
        return topNResult
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename
        print(f"\033[1;31mError in {file_name} at line {line_number}: {e}\033[0m")
        logging.error(f"Error in {file_name} at line {line_number}: {e}")
