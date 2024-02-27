import linecache
import pickle
import argparse
import os
import re
import shutil
import lizard
import numpy as np

from halstead_feature import halstead_cal

# 取消np输出时长度限制
np.set_printoptions(threshold=np.inf)

# 读取一个文件夹，返回里面所有的文件名
def get_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        return dirs
    return []


# 加载文件
def checkAndLoad(root, param):
    dump_path = os.path.join(root, param)
    if os.path.exists(dump_path):
        f = open(dump_path, 'rb')
        content = pickle.load(f)
        f.close()
        return content
    return None


# 存储文件
def checkAndSave(root, param, content):
    dump_path = os.path.join(root, param)
    if not os.path.exists(dump_path):
        f = open(dump_path, 'wb')
        pickle.dump(content, f)
        f.close()

# 分割hugeCode中的类
def numJavaFile(hugeCode_path):
    if not os.path.exists(hugeCode_path):
        return -1
    f = open(hugeCode_path, 'r')
    content = f.readlines()
    file_list = []
    for index in range(len(content)):
        if 'package' in content[index]:
            file_list.append(index)
    ver_list = []
    for start_index in range(len(file_list)):
        tmp = []
        tmp.append(file_list[start_index])
        if start_index == len(file_list) - 1:
            tmp.append(len(content) - 1)
        else:
            tmp.append(file_list[start_index + 1] - 1)
        ver_list.append(tmp)
    f.close()
    return ver_list, content


# 拿到CoverageMatrix
def CoverageMatrix_File(CoverageMatrix_path):
    if not os.path.exists(CoverageMatrix_path):
        return -1
    # 打开二进制文件
    with open(CoverageMatrix_path, 'rb') as f:
        # 反序列化对象，将文件中数据解析为python对象
        CoverageMatrix = pickle.load(f)
        f.close()
    return CoverageMatrix

# 拿到HugeToFile和所有的类名
def HugeToFile_file(ver_list,HugeToFile_path):
    if not os.path.exists(HugeToFile_path):
        return -1
    f = open(HugeToFile_path, 'r')
    HugeToFile = f.readlines()
    f.close()
    class_name = []
    for file_index in ver_list:
        line_txt = HugeToFile[file_index[0]]
        tmp_name = line_txt.split('.java')[0].split('/')[-1]
        class_name.append(tmp_name)
    return class_name, HugeToFile

# 拿到所有的包名和含有通配符的包名
def getPackageName(content):
    package_name = []
    package_name_all = []
    for line in content:
        if 'package' in line:
            tmp_package = line.split('\n')[0].split(' ')[1]
            end = tmp_package.rfind('.')
            tmp_all = tmp_package[0:end] + '.*;'
            package_name.append(tmp_package)
            package_name_all.append(tmp_all)
    return package_name,package_name_all

# 拿到测试类的内容
def testCaseContent_file(testCaseContent_path):
    if not os.path.exists(testCaseContent_path):
        return -1
    # 打开二进制文件
    with open(testCaseContent_path, 'rb') as f:
        # 反序列化对象，将文件中数据解析为python对象
        testCaseContent = pickle.load(f)
        f.close()
    return testCaseContent


#------------------------以下为特征--------------------------

# 计算复杂度
def cal_fcci(ver_list, content):

    fea_list = np.zeros((14, len(content)))
    keys = ['parameters','token_count','top_nesting_level','h_N','h_U','h_V','h_D','h_E','h_B','h_T','h_L','number_of_lines','loc_executable','cyclomatic_complexity']
    # 计算java文件特征
    for file_index in ver_list:
        fun_con_str = ''
        fun_con_list = []
        for index in range(file_index[0], file_index[1] + 1):
            fun_con_str += content[index]
            fun_con_list.append(content[index].strip())

        fun_list = lizard.analyze_file.analyze_source_code("test.java", fun_con_str).function_list
        for function_index in fun_list:
            code_info = {}
            tmp = function_index.__dict__
            h, Ioc_blank = halstead_cal(fun_con_list)
            code_info['parameters'] = len(tmp['full_parameters'])
            code_info['token_count'] = tmp['token_count']
            code_info['top_nesting_level'] = tmp['top_nesting_level']
            code_info['h_N'] = h['h_N']
            code_info['h_U'] = h['h_U']
            code_info['h_V'] = h['h_V']
            code_info['h_D'] = h['h_D']
            code_info['h_E'] = h['h_E']
            code_info['h_B'] = h['h_B']
            code_info['h_T'] = h['h_T']
            code_info['h_L'] = h['h_L']
            code_info['number_of_lines'] = tmp['end_line'] - tmp['start_line'] + 1
            code_info['loc_executable'] = tmp['nloc']
            code_info['cyclomatic_complexity'] = tmp['cyclomatic_complexity']

            for key_index in range(len(keys)):
                for line_index in range(file_index[0]+tmp['start_line'] - 1, file_index[0]+tmp['end_line']):
                    fea_list[key_index][line_index] = code_info[keys[key_index]]

    return fea_list


# 计算语句出度
def cal_outdegree(content):
    list = []
    for line_index in range(len(content)):
        line_txt = content[line_index]
        if line_txt.__contains__('package') or line_txt.__contains__('import') or line_txt.__contains__('class'):
            outdegree = 0
        elif line_txt.__contains__(' if ') or line_txt.__contains__(' if('):
            outdegree = 2
        elif line_txt.__contains__(' for ') or line_txt.__contains__(' for('):
            outdegree = 2
        elif line_txt.__contains__(' while ') or line_txt.__contains__(' while('):
            outdegree = 2
        elif line_txt.__contains__(' switch ') or line_txt.__contains__(' switch('):
            num = 0
            tmp = line_index+1
            while(True):
                stat = content[tmp]
                num = num + stat.count('case')
                num = num + stat.count('default')
                left = stat.count('{')
                right = stat.count('}')
                if left+1 == right:
                    break
                tmp = tmp + 1
            outdegree = num
        else:
            outdegree = 1
        list.append(outdegree)
    return np.array(list)


# 计算语句入度
def cal_indegree(content):
    list = []
    for line_txt in content:
        if line_txt.__contains__('package') or line_txt.__contains__('import') or line_txt.__contains__('class'):
            indegree = 0
        elif line_txt.__contains__(' for ') or line_txt.__contains__(' for('):
            indegree = 2
        elif line_txt.__contains__(' while ') or line_txt.__contains__(' while('):
            indegree = 2
        elif line_txt.__contains__('}while ') or line_txt.__contains__('} while('):
            indegree = 1
        else:
            indegree = 1
        list.append(indegree)
    return np.array(list)


# 测试套件中有多少个测试用例覆盖到变异语句
def cal_numTestCovered(content,CoverageMatrix):
    list = []
    for i in range(len(content)): #hugeCode总行数
        ans = 0
        for j in range(len(CoverageMatrix)):  # 测试用例数
            ans += CoverageMatrix[j][i]

        list.append(ans)

    return np.array(list)


# 变异语句的类型
# 1:判断语句
# 2:循环语句
# 3:函数返回语句
# 4:函数调用语句
# 5:赋值语句
# 6:其他语句(函数声明等)
def cal_typeStatement(content):
    list = []
    # 对语句进行判断
    # 判断语句
    pattern1 = re.compile('if|switch|case')
    # 循环语句
    pattern2 = re.compile('while|for')
    # 函数返回语句
    pattern3 = re.compile('return')
    # 函数调用语句
    pattern4 = re.compile("\..+\(.*\)")
    # 赋值语句
    pattern5 = re.compile("=")
    for line_txt in content:
        if pattern1.findall(line_txt):
            list.append(1)
        elif pattern2.findall(line_txt):
            list.append(2)
        elif pattern3.findall(line_txt):
            list.append(3)
        elif pattern4.findall(line_txt):
            list.append(4)
        elif pattern5.findall(line_txt):
            list.append(5)
        else:
            list.append(6)
    return np.array(list)


# 继承结构中从变异类到根类的路径的最大长度
def cal_depInheritance(class_name,ver_list,content):
    list = []
    tmp_list = []
    for name in class_name:
        class_map = {}
        for line in content:
            if 'class' in line and 'extends' in line:
                tmp = line.split('extends')
                tmp_class = tmp[0].strip(' ').split(' ')[-1]
                tmp_extend = tmp[1].strip(' ').strip('\n').split(' ')[0]
                class_map[tmp_class] = tmp_extend

        ans = 0
        tmp_name = class_map.get(name)
        while tmp_name != None:
            tmp_name = class_map.get(tmp_name)
            ans += 1
        tmp_list.append(ans)

    i = 0
    for file_index in ver_list:
        for line_index in range(file_index[0] , file_index[1]+1):
            list.append(tmp_list[i])
        i += 1

    return np.array(list)


# 变异类的直接子类总数
def cal_numChildren(class_name,content,ver_list):
    list = []
    tmp_list = []
    for name in class_name:
        ans = 0
        for line in content:
            find_name = line.find(' '+name+' ')
            find_extends = line.find('extends')
            if find_name < find_extends  and find_extends != -1 and find_name != -1:
                ans += 1
        tmp_list.append(ans)

    i = 0
    for file_index in ver_list:
        for line_index in range(file_index[0], file_index[1] + 1):
            list.append(tmp_list[i])
        i += 1

    return np.array(list)


# 变异包外依赖包内类的类数
def cal_Ca(content,package_name,package_name_all,ver_list):
    list = []
    tmp_list = []

    for index in range(len(package_name)):
        num = 0
        for line in content:
            if 'import {}'.format(package_name[index]) == line or 'import {}'.format(package_name_all[index]) == line:
                num += 1
        tmp_list.append(num)

    i = 0
    for file_index in ver_list:
        for line_index in range(file_index[0], file_index[1] + 1):
            list.append(tmp_list[i])
        i += 1

    return np.array(list)


# 变异包内依赖包外类的类的数量
def cal_Ce(content,ver_list):
    list = []
    tmp_list = []
    for file_index in ver_list:
        num = 0
        for line_index in range(file_index[0], file_index[1] + 1):
            if 'import' in content[line_index]:
                num += 1
        tmp_list.append(num)

    i = 0
    for file_index in ver_list:
        for line_index in range(file_index[0], file_index[1] + 1):
            list.append(tmp_list[i])
        i += 1

    return np.array(list)


# 包装对变化的弹性的指标，根据 Ca 和 Ce 值计算，即 Ce/(Ce + Ca),如果Ca=Ce=0，那么就直接设定为0
def cal_instability(Ca,Ce,content):
    list = []
    for index in range(len(content)):
        sum = Ce[index] + Ca[index]
        if sum == 0:
            list.append(0)
        else:
            tmp = Ce[index] / sum
            list.append(tmp)

    return np.array(list)


# 测试方法中覆盖每个变异体的断言总数
def cal_numMutantAssertion(content,CoverageMatrix,testCaseContent):
    list = []
    for i in range(len(content)):
        ans = 0
        cov_info = []

        for j in range(len(CoverageMatrix)):
            if CoverageMatrix[j][i] != 0:
                cov_info.append(j)

        for j in range(len(cov_info)):
            num = cov_info[j]
            for k in range(len(testCaseContent[num])):
                line = testCaseContent[num][k].strip('\n')
                if 'assert' in line:
                    ans += 1

        list.append(ans)
    return np.array(list)


# 变异类对应的测试类内部的测试断言总数
def cal_numClassAssertion(numMutantAssertion,ver_list):
    list = []
    for file_index in ver_list:
        sum = 0
        for line_index in range(file_index[0], file_index[1] + 1):
            sum += numMutantAssertion[line_index]
        for line_index in range(file_index[0], file_index[1] + 1):
            list.append(sum)

    return np.array(list)


# 变异方法的返回类型
# -1:不在方法内
# 1: void型
# 2: byte型
# 3: short型
# 4: int型
# 5: long型
# 6: float型
# 7: double型
# 8: char型
# 9: boolean型
# 10: String型
# 11: 数组等类型
# 12: 构造函数
# 13: 其他
def cal_typeReturn(content,ver_list):
    list = [-1] * len(content)
    for file_index in ver_list:

        fun_con_str = ''
        for index in range(file_index[0], file_index[1] + 1):
            fun_con_str += content[index]
        fun_lizard = lizard.analyze_file.analyze_source_code("test.java", fun_con_str)
        if len(fun_lizard.function_list)==0:
            continue

        for i in range(len(fun_lizard.function_list)):
            fun_dict = fun_lizard.function_list[i].__dict__
            start_index = file_index[0]-1
            start_line = fun_dict['start_line']
            end_line = fun_dict['end_line']
            tmp_name = fun_dict['name'].split(':')[-1]

            return_type = content[start_index+start_line].split(tmp_name)[0].split(' ')[-2]
            if return_type == "void":
                ans = 1
            elif return_type == "byte":
                ans = 2
            elif return_type == "short":
                ans = 3
            elif return_type == "int":
                ans = 4
            elif return_type == "long":
                ans = 5
            elif return_type == "float":
                ans = 6
            elif return_type == "double":
                ans = 7
            elif return_type == "char":
                ans = 8
            elif return_type == "boolean":
                ans = 9
            elif return_type == "String":
                ans = 10
            elif return_type == "List" or return_type == "LinkedList" or return_type == "Map" or return_type == "LinkedList":
                ans = 11
            elif return_type == "public":
                ans = 12
            else:
                ans = 13
            for j in range(start_index+start_line, start_index+end_line+1):
                list[j] = ans

    return np.array(list)


# 继承结构中从变异类到根类的路径的最大长度
def cal_depNestblock(content,ver_list):
    list = []
    for file_index in ver_list:
        ans = 0
        num = 0
        for line_index in range(file_index[0], file_index[1] + 1):
            if '{' in content[line_index]:
                for i in content[line_index]:
                    if i == '{':
                        num += 1
                if num > ans:
                    ans = num
            if '}' in content[line_index]:
                for i in content[line_index]:
                    if i == '}':
                        num -= 1
        ans -= 2
        if ans < 0:
            ans = 0
        for line_index in range(file_index[0], file_index[1] + 1):
            list.append(ans)

    return np.array(list)


# 计算全部
def cal_all(pro_path, res_path):
    # 获取全部程序
    pros = get_folder(pro_path)
    for pro_name in pros:
        # if pro_name != 'Closure':
        #     continue
        print(pro_name)
        pro_path = os.path.join(pro_path, pro_name)
        # 创建结果文件
        res_pro = os.path.join(res_path, pro_name)
        if not os.path.exists(res_pro):
            os.mkdir(res_pro)
        # 获取程序全部版本
        vers = get_folder(pro_path)
        for ver_name in vers:
            # if ver_name == '50b':
            #     continue
            print(ver_name)

            ver_path = os.path.join(pro_path, ver_name)
            # 得到CoverageMatrix
            CoverageMatrix_path = os.path.join(ver_path,'CoverageMatrix.in')
            CoverageMatrix = CoverageMatrix_File(CoverageMatrix_path)

            print(CoverageMatrix)
            exit(1)
            hugeCode_path = os.path.join(ver_path,'hugeCode.txt')
            if not os.path.exists(hugeCode_path):
                continue
            result = cal_feature(res_pro, ver_name, ver_path)
            # break
            print(ver_name,"end")


# 计算全部
def cal_feature(res_pro, ver_name, ver_path):

    # 存储结果
    res_ver = os.path.join(res_pro, ver_name)
    if not os.path.exists(res_ver):
        os.mkdir(res_ver)

    static_fea = checkAndLoad(res_ver, 'static_fea')
    if static_fea is not None:
        return 'success'

    # 得到hugeCode
    hugeCode_path = os.path.join(ver_path, 'hugeCode.txt')
    ver_list, content = numJavaFile(hugeCode_path)
    # 得到CoverageMatrix
    CoverageMatrix_path = os.path.join(ver_path,'CoverageMatrix.in')
    CoverageMatrix = CoverageMatrix_File(CoverageMatrix_path)
    print(CoverageMatrix)
    exit(1)
    # 得到HugeToFile和所有的类名
    HugeToFile_path = os.path.join(ver_path,'HugeToFile.txt')
    class_name, HugeToFile = HugeToFile_file(ver_list,HugeToFile_path)
    # 拿到所有的包名和含有通配符的包名
    package_name, package_name_all = getPackageName(content)
    # 拿到测试类的内容
    testCaseContent_path = os.path.join(ver_path,'testCaseContent.in')
    testCaseContent = testCaseContent_file(testCaseContent_path)

    fea_list = cal_fcci(ver_list, content)
    indegree = cal_indegree(content)
    outdegree = cal_outdegree(content)
    numTestCovered = cal_numTestCovered(content,CoverageMatrix)
    typeStatement = cal_typeStatement(content)
    depInheritance = cal_depInheritance(class_name,ver_list,content)
    numChildren = cal_numChildren(class_name,content,ver_list)
    Ca = cal_Ca(content,package_name,package_name_all,ver_list)
    Ce = cal_Ce(content,ver_list)
    instability = cal_instability(Ca,Ce,content)
    numMutantAssertion = cal_numMutantAssertion(content, CoverageMatrix, testCaseContent)
    numClassAssertion = cal_numClassAssertion(numMutantAssertion, ver_list)
    typeReturn = cal_typeReturn(content, ver_list)
    depNestblock = cal_depNestblock(content, ver_list)

    res = {}
    res['fcci'] = fea_list
    res['indegree'] = indegree
    res['outdegree'] = outdegree
    res['numTestCovered'] = numTestCovered
    res['typeStatement'] = typeStatement
    res['depInheritance'] = depInheritance
    res['numChildren'] = numChildren
    res['Ca'] = Ca
    res['Ce'] = Ce
    res['instability'] = instability
    res['numMutantAssertion'] = numMutantAssertion
    res['numClassAssertion'] = numClassAssertion
    res['typeReturn'] = typeReturn
    res['depNestblock'] = depNestblock

    checkAndSave(res_ver, 'static_fea', res)

    return 'success'



if __name__ == "__main__":


    pro_path = '/home/public/outputClean'
    res_path = '/home/public/restwo'

    cal_all(pro_path, res_path)


