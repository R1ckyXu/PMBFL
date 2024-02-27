import copy
import csv
import linecache
import os.path
import sys
import time
from multiprocessing import Pool
#import fuzzyCal

from tqdm import trange

import Tool_io
import Tool_localization


_formulaList={"dstar", "jaccard", "ochiai"}
_CCstrategyList={"clean", "exchange", "relabel"}



def getSuspiciousnessScoreFactorSimple(versionPath, covMatrix, formulaSus_origin):
    print("SS start")
    formulaSus = formulaSus_origin
    SS_ALL_t = Tool_io.checkAndLoad(versionPath[1], "data_origin_SS")
    if SS_ALL_t != None:
        SS_ALL_t, formulaSus, flag = Tool_io.add_del_formula(SS_ALL_t,formulaSus_origin,versionPath[1],'data_origin_SS')
        if flag == 0:
            return SS_ALL_t

    SS_ALL = {}
    for algorithm_k in formulaSus:
        SS = {}
        for case_index in trange(len(covMatrix)):
            Sh_Num=0
            Sh_Sum=0
            Sl_Num=0
            Sl_Sum = 0
            for key in formulaSus[algorithm_k]:
                if covMatrix[case_index][key]==1:
                    if formulaSus[algorithm_k][key]>=0.5:
                        Sh_Num += 1
                        Sh_Sum += formulaSus[algorithm_k][key]
                    else:
                        Sl_Num += 1
                        Sl_Sum += formulaSus[algorithm_k][key]
            if Sh_Num > 0:
                SS[case_index] = Sh_Sum/Sh_Num
            else:
                if Sl_Num == 0:
                    SS[case_index] = 0
                else:
                    SS[case_index] = Sl_Sum / Sl_Num
        SS_ALL[algorithm_k] = SS
    # 若原结果存在，且有新增怀疑度公式，将新结果拼接后重新存储
    if SS_ALL_t is not None:
        for add_index in SS_ALL:
            SS_ALL_t[add_index] = SS_ALL[add_index]
    else:
        SS_ALL_t = SS_ALL
    Tool_io.checkAndSave(versionPath[1], "data_origin_SS", SS_ALL_t)
    print("SS end")
    return SS_ALL_t


def getCoverageRatioFactor(versionPath, covMatrix,formulaSus_origin):
    print("CR start")
    formulaSus = formulaSus_origin
    CR_ALL_t = Tool_io.checkAndLoad(versionPath[1], "data_origin_CR")
    if CR_ALL_t != None:
        CR_ALL_t, formulaSus, flag = Tool_io.add_del_formula(CR_ALL_t, formulaSus_origin, versionPath[1], 'data_origin_CR')
        if flag == 0:
            return CR_ALL_t

    CR_ALL = {}
    for algorithm_k in formulaSus:
        CR = {}
        for case_index in trange(len(covMatrix)):
            #if inVector[case_index] == 0:
            S_num = 0
            Sp_num = 0
            for key in formulaSus[algorithm_k]:
                #怀疑分数在0.5-1之间的语句数量
                if(formulaSus[algorithm_k][key] >= 0.5):
                    S_num += 1
                    # 计算怀疑分数在0.5-1之间的并且被执行的语句数量
                    if covMatrix[case_index][key] == 1:
                        Sp_num += 1
            #计算CR值
            if S_num == 0:
                CR[case_index] = 0
            else:
                CR[case_index] = Sp_num / S_num
        CR_ALL[algorithm_k] = CR
    # 若原结果存在，且有新增怀疑度公式，将新结果拼接后重新存储
    if CR_ALL_t is not None:
        for add_index in CR_ALL:
            CR_ALL_t[add_index] = CR_ALL[add_index]
    else:
        CR_ALL_t = CR_ALL
    Tool_io.checkAndSave(versionPath[1], "data_origin_CR", CR_ALL_t)
    return CR_ALL_t


def getSimilarityFactor(versionPath,covMatrix,inVector,formulaSus_origin):
    print("SF start")
    # 若存在SF结果，则直接返回
    formulaSus = formulaSus_origin
    SF_ALL_t = Tool_io.checkAndLoad(versionPath[1], "data_origin_SF")
    if SF_ALL_t != None:
        SF_ALL_t, formulaSus, flag = Tool_io.add_del_formula(SF_ALL_t, formulaSus_origin, versionPath[1], 'data_origin_SF')
        if flag == 0:
            return SF_ALL_t

    SF_ALL = {}
    for algorithm_k in formulaSus:
        SF = {}
        Ef = []
    #计算失败测试用例的加权向量
        for case_failed in range(len(covMatrix)):
            if inVector[case_failed] == 1:
                fi = copy.deepcopy(covMatrix[case_failed])
                for key in formulaSus[algorithm_k]:
                    fi[key] *= formulaSus[algorithm_k][key]
                Ef.append(fi)
        for case_index in trange(len(covMatrix)):
            #if inVector[case_index] == 0:
            #计算Ep的加权向量
            Ep = copy.deepcopy(covMatrix[case_index])
            for key in formulaSus[algorithm_k]:
                Ep[key] *= formulaSus[algorithm_k][key]
            #Efi和Ep距离初始值为最大值，也就是程序语句数
            distance = len(covMatrix[case_index])
            # 计算Efi和Ep之间的最短距离
            for fail_index in range(len(Ef)):
                sum = 0
                for index in range(len(Ef[fail_index])):
                    sum = sum+(Ef[fail_index][index]-Ep[index])**2
                if sum**0.5 < distance:
                    distance = sum**0.5
            #计算SF值
            if distance == 0:
                SF[case_index] = 0
            else:
                SF[case_index] = 1 / distance
        SF_ALL[algorithm_k] = SF

    # 若原结果存在，且有新增怀疑度公式，将新结果拼接后重新存储
    if SF_ALL_t is not None:
        for add_index in SF_ALL:
            SF_ALL_t[add_index] = SF_ALL[add_index]
    else:
        SF_ALL_t = SF_ALL
    Tool_io.checkAndSave(versionPath[1], "data_origin_SF", SF_ALL_t)
    return SF_ALL_t


def getFaultMaskingFactor(versionPath, covMatrix, formulaSus_origin, target):
    print("FM start")
    # 若存在SF结果，则直接返回
    # 若存在SF结果，则直接返回
    formulaSus = formulaSus_origin
    FM_ALL_t = Tool_io.checkAndLoad(versionPath[1], "data_origin_FM")
    if FM_ALL_t != None:
        FM_ALL_t, formulaSus, flag = Tool_io.add_del_formula(FM_ALL_t, formulaSus_origin, versionPath[1], 'data_origin_FM')
        if flag == 0:
            return FM_ALL_t

    #impact factor
    operators={
        '>':0.79,
        '<':0.79,
        '=':0.79,
        '>=':0.79,
        '<=':0.79,
        '+':0.08,
        '-':0.08,
        '*':0.08,
        '/':0.08,
        '%':0.38,
    }
    FM_ALL = {}
    for algorithm_k in formulaSus:
        FM = {}
        for case_index in trange(len(covMatrix)):
            #if inVector[case_index] == 0:
            for stat_index in range(len(covMatrix[case_index])):
                if covMatrix[case_index][stat_index] == 1:
                    #查找怀疑度大于0.5的第一条被执行过的语句
                    if(formulaSus[algorithm_k][stat_index])>0.5:
                        #查找怀疑度大于0.5的第一条被执行过的语句 的下一条语句
                        list_index = stat_index+1
                        #遍历之后的语句
                        sum_op = 0
                        while list_index < len(covMatrix[case_index]):
                            if covMatrix[case_index][list_index] == 1:
                                text = linecache.getline(target,list_index+1)
                                #取 operators 最大值
                                impact_factor  = 0
                                for k,v in operators.items():
                                 if text.find(k):
                                    if v > impact_factor:
                                        impact_factor = v
                                #语句impact_factor求和
                                sum_op += impact_factor
                            list_index += 1
                        FM[case_index] = sum_op
                        break
                    else:
                        FM[case_index] = 0
                else:
                    FM[case_index] = 0
            FM_ALL[algorithm_k] = FM
    # 若原结果存在，且有新增怀疑度公式，将新结果拼接后重新存储
    if FM_ALL_t is not None:
        for add_index in FM_ALL:
            FM_ALL_t[add_index] = FM_ALL[add_index]
    else:
        FM_ALL_t = FM_ALL
    Tool_io.checkAndSave(versionPath[1], "data_origin_FM", FM_ALL_t)
    return FM_ALL_t



# 执行程序
def execution(param):
    versionPath = param[0]
    error_pro_ver = param[1]
    # 获得覆盖信息，测试用例结果
    covMatrix, fault, inVector, failN, passN, realCC, failIndex, trueCC = Tool_io.readFile(versionPath, error_pro_ver)
    print("s")
    # 若结果为空
    if covMatrix == None:
        return None
    # 判断cc是否数量为0
    if len(realCC) == 0:
        f_error = open(os.path.join(error_pro_ver, 'error_loc.txt'), 'a+')
        f_error.writelines(versionPath[0] + " 该版本无cc\r\n")
        f_error.close()
    statement_num = len(covMatrix[0])
    case_num = len(covMatrix)
    # 所有怀疑度公式
    sus_formulas = Tool_localization.deal_suspicion_formula()
    # 计算怀疑度分数
    sus_score = Tool_localization.statement_sus(sus_formulas,case_num, statement_num, covMatrix, inVector, versionPath)
    # print(sus_formulas)
    # 计算SS
    print(versionPath)
    SS = getSuspiciousnessScoreFactorSimple(versionPath, covMatrix, sus_score)
    # 计算CR
    print(versionPath)
    CR = getCoverageRatioFactor(versionPath, covMatrix, sus_score)
    # 计算SF
    print(versionPath)
    SF = getSimilarityFactor(versionPath, covMatrix, inVector, sus_score)
    # 计算FM
    print(versionPath)
    # target = os.path.join(versionPath[1], "hugeCodeCopy.txt")
    # FM = getFaultMaskingFactor(versionPath, covMatrix, sus_score, target)
    # 归一化特征
    # res_nor = Tool_localization.normalization(SS, CR, SF, FM, versionPath)
    return "success"


def cal_time(path,cur_pro,current_timestamp,end_timestamp,save):

    vers = get_folder(path)
    tis = 0
    for ver in vers:
        ver_path = os.path.join(path, ver)
        file_path = os.path.join(ver_path, 'fuzzy_knn_test3')
        if os.path.exists(file_path):
            tis = tis+1
    avg_time = (end_timestamp-current_timestamp)/tis
    with open(save, 'a+', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([cur_pro,avg_time])
    return tis


def get_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        return dirs
    return []

if __name__ =="__main__":



    # linux MLCCI
    root = '/home/tianshuaihua/outputClean'
    data = '/home/tianshuaihua/tpydata'
    error_pro_ver = '/home/tianshuaihua/error'
    res_path = '/home/tianshuaihua/res'

    # 获取程序路径
    res = Tool_io.create_data_folder(root,data)
    save = '/home/tianshuaihua/base_res/time.csv'
    for index in res:
        cur_pro = os.path.basename(index)
        if cur_pro != 'Closure':
            continue
        pool = Pool(processes=8)
        current_timestamp = time.time()
        for ver in res[index]:
            print(ver)
            pro_name = os.path.basename(index)
            param = []
            param.append(ver)
            param.append(error_pro_ver)
            pool.apply_async(execution, (param,))

        pool.close()
        pool.join()

        end_timestamp = time.time()
        print("current program end")

