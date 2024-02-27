import os
import json
from collections import Counter
import json
projectList = {
    "Chart": 26,
    # "Cli": 39,
    "Closure": 176,
    # "Codec": 18,
    # # "Collections": 4,
    # "Compress": 47,
    # "Csv": 16,
    # "Gson": 18,
    # "JacksonCore": 26,
    # "JacksonDatabind": 112,
    # "JacksonXml": 6,
    # "Jsoup": 93,
    # "JxPath": 22,
    # "Lang": 65,
    # "Math": 106,
    # "Mockito": 38,
    "Time": 27,
}

with open("./failVersion.json", "r") as f:
    failVersion = json.load(f)

# 自动创建不存在的目录
def checkAndCreateDir(Path):
    if not os.path.exists(Path):
        os.mkdir(Path)

def countTonN(root_path, project, mode):
    """
    遍历指定目录下所有子目录是否存在指定文件,如果存在则使用json.load读取文件内容
    """
    projectStatistics = dict()
    print(project,mode.split('Function')[1])
    for version in os.listdir(root_path + "/" + project):
        if not version.endswith('b'):
            continue
        if not failVersion.get(project) is None and version in failVersion[project]:
            continue
        print(version)
        for root, dirs, files in os.walk(root_path + "/" + project + "/" + version + "/" + mode):
            # 遍历当前目录下的所有文件
            for filename in files:
                if filename not in projectStatistics:
                    projectStatistics[filename] = dict()
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for key in data.keys():
                    for line in data[key].keys():
                        for item in data[key][line].keys():
                            if item not in projectStatistics[filename]:
                                projectStatistics[filename][item] = Counter({'top1': 0, 'top2': 0, 'top3': 0, 'top4': 0, 'top5': 0, 'top10': 0, 'top15':0, 'top20':0})
                            if data[key][line][item] <= 20 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top20'] += 1
                            if data[key][line][item] <= 15 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top15'] += 1
                            if data[key][line][item] <= 10 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top10'] += 1
                            if data[key][line][item] <= 5 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top5'] += 1
                            if data[key][line][item] <= 4 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top4'] += 1
                            if data[key][line][item] <= 3 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top3'] += 1
                            if data[key][line][item] <= 2 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top2'] += 1
                            if data[key][line][item] <= 1 and data[key][line][item] >= 0:
                                projectStatistics[filename][item]['top1'] += 1
    if 'BasedSbfl' in mode:
        project = project + '_basedSBFL'
        mode = mode.split('_')[0]
    checkAndCreateDir('./predTopN/')
    checkAndCreateDir('./predTopN/' + mode)
    with open('./predTopN/' + mode + '/' + project, 'w') as f:
        f.write(json.dumps(projectStatistics, indent=2))

def countMAR(root_path, project, mode):
    projectStatistics = dict()
    count = 0
    for version in os.listdir(root_path + "/" + project):
        if not failVersion.get(project) is None and version in failVersion[project]:
            continue
        if os.path.exists(root_path + "/" + project + "/" + version + "/" + mode):
            count += 1
        for root, dirs, files in os.walk(root_path + "/" + project + "/" + version + "/" + mode):
            # 遍历当前目录下的所有文件
            for filename in files:
                if filename not in projectStatistics:
                    projectStatistics[filename] = dict()
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for key in data.keys():
                    if projectStatistics[filename].get(key) is None:
                        projectStatistics[filename][key] = 0
                    projectStatistics[filename][key] += data[key]
    
    for filename in projectStatistics.keys():
        for key in projectStatistics[filename].keys():
            projectStatistics[filename][key] /= count
    # print(projectStatistics)
    checkAndCreateDir('./predMAR/')
    if 'BasedSbfl' in mode:
        project = project + '_basedSBFL'
    with open("./predMAR/" + project, 'w') as f:
        f.write(json.dumps(projectStatistics, indent=2))
    
    return

def countMFR(root_path, project, mode):
    projectStatistics = dict()
    count = 0
    for version in os.listdir(root_path + "/" + project):
        if not failVersion.get(project) is None and version in failVersion[project]:
            continue
        if os.path.exists(root_path + "/" + project + "/" + version + "/" + mode):
            count += 1
        for root, dirs, files in os.walk(root_path + "/" + project + "/" + version + "/" + mode):
            # 遍历当前目录下的所有文件
            for filename in files:
                if filename not in projectStatistics:
                    projectStatistics[filename] = dict()
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for key in data.keys():
                    if projectStatistics[filename].get(key) is None:
                        projectStatistics[filename][key] = 0
                    projectStatistics[filename][key] += data[key]
    
    for filename in projectStatistics.keys():
        for key in projectStatistics[filename].keys():
            projectStatistics[filename][key] /= count
    # print(projectStatistics)
    checkAndCreateDir('./predMFR/')
    if 'BasedSbfl' in mode:
        project = project + '_basedSBFL'
    with open("./predMFR/" + project, 'w') as f:
        f.write(json.dumps(projectStatistics, indent=2))
    
    return


def countModelMetrics(root_path, project):
    projectStatistics = dict()
    count = 0
    for version in os.listdir(root_path + "/" + project):
        if not failVersion.get(project) is None and version in failVersion[project]:
            continue
        if os.path.exists(root_path + "/" + project + "/" + version + "/ModelMetrics"):
            count += 1
        for root, dirs, files in os.walk(root_path + "/" + project + "/" + version + "/ModelMetrics"):
            # 遍历当前目录下的所有文件
            for filename in files:
                if filename not in projectStatistics:
                    projectStatistics[filename] = dict()
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for key in data.keys():
                    if projectStatistics[filename].get(key) is None:
                        projectStatistics[filename][key] = 0
                    projectStatistics[filename][key] += data[key]
    
    for filename in projectStatistics.keys():
        for key in projectStatistics[filename].keys():
            projectStatistics[filename][key] /= count
    # print(projectStatistics)
    with open("./ModelMetrics/" + project, 'w') as f:
        f.write(json.dumps(projectStatistics, indent=2))
    
    return


if __name__ =="__main__":
    rootdir = "/home/fanluxi/pmbfl/FOMfaultlocalizationResult/"
    for project in projectList.keys():
        # PMBFL
        countTonN(rootdir, project, 'predTopNFunctionBest')
        countTonN(rootdir, project, 'predTopNFunctionAverage')
        countTonN(rootdir, project, 'predTopNFunctionWorst')
        print('TOP N finish')
        countMAR(rootdir, project,'predMAR')
        print('MAR finish')
        countMFR(rootdir, project,'predMFR')
        print('MFR finish')
        countModelMetrics(rootdir, project)
        print('ModelMetrics finish')
