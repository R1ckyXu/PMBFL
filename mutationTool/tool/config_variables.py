import json
from tool.mbfl_formulas import dstar, ochiai, gp13, op2, jaccard, russell, turantula, naish1, binary, crosstab, dstar2
with open('config.json', 'r') as configFile:
    configData = json.load(configFile)

tempSrcPath = configData['tempSrcPath']
tpydataPath = configData['tpydataPath']
outputCleanPath = configData['outputCleanPath']
djSrcPath = configData['djSrcPath']
mutantsFilePath = configData['mutantsFilePath']
faliingTestOutputPath = configData['faliingTestOutputPath']
faultlocalizationResultPath = configData['faultlocalizationResultPath']
FOMprocessedData = configData['FOMprocessedData']
SOMprocessedData = configData['SOMprocessedData']
SOMfaultlocalizationResultPath = configData['SOMfaultlocalizationResultPath']

sbflMethod = ['dstar', 'dstar_sub_one', 'ochiai', 'ochiai_sub_one', 'ochiai_sub_two', 'gp13', 'gp13_sub_one', 'gp13_sub_two',
              'op2', 'op2_sub_one', 'op2_sub_two', 'jaccard', 'jaccard_sub_one', 'russell', 'russell_sub_one', 'turantula',
              'turantula_sub_one', 'naish1', 'binary', 'crosstab', 'dstar2']

sourcePath = {
    'Chart': {'26': 'source'},
    'Cli': {'29': 'src/java', '39': 'src/main/java'},
    'Closure': {'176': 'src'},
    'Codec': {'10': 'src/java', '18': 'src/main/java'},
    'Compress': {'47': 'src/main/java'},
    'Csv': {'16': 'src/main/java'},
    'Gson': {'18': 'gson/src/main/java'},
    'JacksonCore': {'26': 'src/main/java'},
    'JacksonDatabind': {'112': 'src/main/java'},
    'JacksonXml': {'6': 'src/main/java'},
    'Jsoup': {'93': 'src/main/java'},
    'JxPath': {'22': 'src/java'},
    'Lang': {'35': 'src/main/java', '65': 'src/java'},
    'Math': {'84': 'src/main/java', '106': 'src/java'},
    'Mockito': {'38': 'src'},
    'Time': {'27': 'src/main/java'}
}

password = "Van@1999."

project = {
    "Chart": 26,
    "Cli": 39,
    "Closure": 133,
    "Closure": 176,
    "Codec": 18,
    "Collections": 4, # 无文件
    "Compress": 47,
    "Csv": 16,
    "Gson": 18,
    "JacksonCore": 26,
    "JacksonDatabind": 112,
    "JacksonXml": 6,
    "Jsoup": 93,
    "JxPath": 22, # 需要联网变异
    "Lang": 65,
    "Math": 106,
    "Mockito": 38, # 需要联网变异
    "Time": 27
}

mbflMethods = [
    dstar
    # ,dstar_sub_one
    , ochiai
    # ,ochiai_sub_one
    # ,ochiai_sub_two
    , gp13
    # ,gp13_sub_one
    # ,gp13_sub_two
    , op2
    # ,op2_sub_one
    # ,op2_sub_two
    , jaccard
    # ,jaccard_sub_one
    , russell
    # ,russell_sub_one
    , turantula
    # ,turantula_sub_one
    , naish1
    , binary
    , crosstab
    # , dstar2
]


method_names = ['dstar', 'ochiai', 'gp13', 'op2', 'jaccard', 'russell', 'turantula', 'naish1', 'binary', 'crosstab', 'muse']