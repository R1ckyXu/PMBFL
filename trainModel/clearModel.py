import json
import os
import pickle
import shutil

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
    "Lang": 65,
    "Math": 106,
    # "Mockito": 38,
    "Time": 27,
}

with open('../mutationTool/config.json', 'r') as configFile:
    configData = json.load(configFile)
tempSrcPath = configData['tempSrcPath']
tpydataPath = configData['tpydataPath']
outputCleanPath = configData['outputCleanPath']
djSrcPath = configData['djSrcPath']
mutantsFilePath = configData['mutantsFilePath']
faliingTestOutputPath = configData['faliingTestOutputPath']
faultlocalizationResultPath = configData['faultlocalizationResultPath']
FOMprocessedData = configData['FOMprocessedData']

for proj in projectList:
    # 删除模型和模型评价
    path = os.path.join(faultlocalizationResultPath, proj)
    dirs = os.listdir(path)
    for di in dirs:
        if not di.endswith('b'):
            continue
        print(proj,di)
        dModel = os.path.join(path,di,'Model')
        dModelMetrics = os.path.join(path,di,'ModelMetrics')
        dPredSuspicious = os.path.join(path,di,'predSuspicious')
        dPredTopNFunctionAverage = os.path.join(path,di,'predTopNFunctionAverage')
        dPredTopNFunctionBest = os.path.join(path,di,'predTopNFunctionBest')
        dPredTopNFunctionWorst = os.path.join(path,di,'predTopNFunctionWorst')

        dPredSuspicious_BasedSbfl = os.path.join(path,di,'predSuspicious_BasedSbfl')
        dPredTopNFunctionAverage_BasedSbfl = os.path.join(path,di,'predTopNFunctionAverage_BasedSbfl')
        dPredTopNFunctionBest_BasedSbfl = os.path.join(path,di,'predTopNFunctionBest_BasedSbfl')
        dPredTopNFunctionWorst_BasedSbfl = os.path.join(path,di,'predTopNFunctionWorst_BasedSbfl')

        dMAR = os.path.join(path,di,'MAR')
        dMFR = os.path.join(path,di,'MFR')


        dpredMAR = os.path.join(path,di,'predMAR')
        dpredMFR = os.path.join(path,di,'predMFR')

        dpredMAR_BasedSbfl = os.path.join(path,di,'predMAR_BasedSbfl')
        dpredMFR_BasedSbfl = os.path.join(path,di,'predMFR_BasedSbfl')
        if os.path.exists(dModel):
            shutil.rmtree(dModel)
        if os.path.exists(dModelMetrics):
            shutil.rmtree(dModelMetrics)

        if os.path.exists(dPredSuspicious):
            shutil.rmtree(dPredSuspicious)
        if os.path.exists(dPredTopNFunctionAverage):
            shutil.rmtree(dPredTopNFunctionAverage)
        if os.path.exists(dPredTopNFunctionBest):
            shutil.rmtree(dPredTopNFunctionBest)
        if os.path.exists(dPredTopNFunctionWorst):
            shutil.rmtree(dPredTopNFunctionWorst)

        if os.path.exists(dPredSuspicious_BasedSbfl):
            shutil.rmtree(dPredSuspicious_BasedSbfl)
        if os.path.exists(dPredTopNFunctionAverage_BasedSbfl):
            shutil.rmtree(dPredTopNFunctionAverage_BasedSbfl)
        if os.path.exists(dPredTopNFunctionBest_BasedSbfl):
            shutil.rmtree(dPredTopNFunctionBest_BasedSbfl)
        if os.path.exists(dPredTopNFunctionWorst_BasedSbfl):
            shutil.rmtree(dPredTopNFunctionWorst_BasedSbfl)
        
        # if os.path.exists(dMAR):
        #     shutil.rmtree(dMAR)
        # if os.path.exists(dMFR):
        #     shutil.rmtree(dMFR)
        
        if os.path.exists(dpredMAR):
            shutil.rmtree(dpredMAR)
        if os.path.exists(dpredMFR):
            shutil.rmtree(dpredMFR)

        if os.path.exists(dpredMAR_BasedSbfl):
            shutil.rmtree(dpredMAR_BasedSbfl)
        if os.path.exists(dpredMFR_BasedSbfl):
            shutil.rmtree(dpredMFR_BasedSbfl)