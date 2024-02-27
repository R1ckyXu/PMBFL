# PMBFL: Predictive Mutation-Based Fault Localization

## Feature extraction:

The **featureExtraction** file is a tool file for feature extraction. 

- First, put the program to be tested into ". /featureExtraction/test.java".
- Then, run Memory.py to extract features from the program. 
- Finally, run featureExtract.py to extract the features of the test case.



## Generate mutants & SBFL & MBFL:

The **mutationTool** file is used to generate mutants and to locate faults in combination with MBFL and SBFL techniques.

- Mutant generation and fault localization can be performed by running main.py.
- Simply run reCalMetrics.py to perform statistics on the evaluation metrics, and the results will be saved separately under the ". /topN/", ". /MAR/", ". /MFR/".

One thing to note is that if you get a log message about insufficient permissions when running the main method, you may need to go to the ". /mutationTool/tool" folder and modify the permissions of the major script. The specific command is shown below:

```shell
cd . /mutationTool/tool
chmod 777 runMajor.sh
```



## Using PMBFL:

The **trainModel** file contains the PMBFL implementation and statistical methods.

- main.py contains the implementation of PMBFL using various classification model algorithms, open the comments as needed and run main.py.

- You can run count.py to count the results of PMBFL execution, and the results are saved in ". /predTopN", ". /predMAR", ". /predMFR".

- If you want to clear the existing model and statistics you can run clearModel.py. Also, if you want to do multiple experiments remember to clear the model first and then run main.py again to get the latest version of the training model.

  

## Experimental results:

The **result** folder stores all the experimental results including SBFL, MBFL, PMBFL, PMT, HMER, and SELECTIVE. each method has result files with different sampling rates.



## Remarks：

- This tool passed experiment on the "Linux version 3.10.0-957.el7.x86_64".
- python version : 3.10.6
