import pandas as pd 
import numpy as np
import math
import ast

import glob
import os
import random
from time import process_time

from scipy.stats import pearsonr, spearmanr
from scipy.spatial import distance

import warnings
warnings.filterwarnings("ignore")

import sys
from functools import cmp_to_key
from  sklearn.preprocessing import normalize
from ast import literal_eval

def compare(item1, item2):
    if item1 < item2:
        return -1
    elif item1 > item2:
        return 1
    else:
        return 0




def getDiametersDistances(matrixDistances):
    
    diametersMatrix = pd.DataFrame(index=matrixDistances.index, columns=matrixDistances.columns)
    finalDiameters = pd.DataFrame(index=[0], columns=np.arange(0, len(matrixDistances.columns)))
    
    for tup in range(len(matrixDistances)):
        for col in range(len(matrixDistances.columns)):
            
            diametersMatrix.iloc[tup,col] = max(matrixDistances.iloc[tup,col])
            
    for col in range(len(diametersMatrix.columns)):
        finalDiameters.iloc[0,col] = max(diametersMatrix.iloc[:,col])
                         
    return finalDiameters



def generateDistanceMaps(data, function, dir_path):
    
    distanceMatrixValues = pd.DataFrame(index=data.index, columns=data.columns)

    #loops (tup x objs) to iterate each object of dataframe
    for atr in range(len(data.columns)):
        for tup in range(len(data)):
#             # Verify if the choose obj is a missing data
#             # IF NOT missing data, continue the process...
#             # IF YES, choose the next object of dataframe
            if(np.isnan(data.iloc[tup, atr]).any() == False):

                obj = data.iloc[tup, atr]
                objDistance = []

                for i in range(len(data)):

                    #  Verify if the iterate object is missing data
                    if(np.isnan(data.iloc[i,atr]).any()):
                           continue
                    else:
                        if (function == 'euclidean'):
                            # create equation to calculate matrix with euclidean
                            objDistance += [distance.euclidean(obj, data.iloc[i,atr])]

                        elif (function == 'chebyshev'):
                            # create equation to calculate matrix with chebyshev
                            objDistance += [distance.chebyshev(obj, data.iloc[i,atr])]

                        elif (function == 'manhattan'):
                            # create equation to calculate matrix with manhattan/cityblock
                            objDistance += [distance.cityblock(obj, data.iloc[i,atr])]
                                
            else:
                objDistance = np.nan
        
            distanceMatrixValues.iloc[tup, atr] = objDistance
    
    diametersMatrix = getDiametersDistances(distanceMatrixValues)
    
    diametersMatrix.to_pickle(dir_path+'matrix_diameters.pkl')
            
    return distanceMatrixValues


def corDiS(data, correlation , dir_path):
        
    corrMatrix = pd.DataFrame(index = data.columns,columns=data.columns, dtype=float)
        
    for i in range(len(data.columns)):
        for j in range(len(data.columns)):
            p = []
            for k in range(len(data)):
                if(np.isnan(data.iloc[k,j]).any() == False and np.isnan(data.iloc[k,i]).any() == False):

                    if(correlation == 'pearson'):p += [pearsonr(data.iloc[k,i], data.iloc[k,j])[0]]
                        
                    elif(correlation == 'spearman'): p += [spearmanr(data.iloc[k,i], data.iloc[k,j])[0]]
                        
            corrMatrix.iloc[i,j] = (np.sum(p))/len(data)

    corrMatrix.to_pickle(dir_path+'matrix_{}.pkl'.format(correlation))
        
    return corrMatrix


# In[5]:


def normalizeCompatibleAttributes (matrixComp):
    
    # manipulate each columns(attribute) of patient tuple
    for i in range(len(matrixComp)):

        #iterate between each exam            
        fatct_comp = matrixComp.loc[i]['Fact_attributes']
        sum_fatc = sum(matrixComp.iloc[i]['Fact_attributes'])
        
        new_factor = []
        for j in range(len(fatct_comp)):
            new_factor += [fatct_comp[j]/sum_fatc] 
     
        matrixComp.loc[i, 'Fact_norm'] =  str(new_factor)
    matrixComp['Fact_norm'] = matrixComp['Fact_norm'].apply(literal_eval)

    return matrixComp
    
def findCompatibleAttributes(data, matrixCorr, threshold, k_attributes, dir_path, correlation):   

    # Path of output directory
    matrixCompatibleAtr = pd.DataFrame(columns=['Threshold','K_Value','Comp_attributes','Fact_attributes'])

    # Path of matrixTCompatibleAttributes 
    output_path = dir_path+'matrixCompatibility_{}/'.format(correlation)
    try:
        # Create target Directory
        os.mkdir(output_path)
    except FileExistsError:
        pass

    for row in range(len(matrixCorr)): # iterate rows in matrixThreshold 
        list_comp_atr  = []
        list_factc = []
        for col in range(len(matrixCorr.columns)):  # iterate columns in matrixThreshold 
            if(matrixCorr.iloc[row,col] >= threshold and (row is not col) and (len(list_comp_atr) < k_attributes)):

                list_comp_atr  += [col]
                list_factc += [matrixCorr.iloc[row,col]]

        matrixCompatibleAtr.loc[len(matrixCompatibleAtr)] = (threshold, k_attributes,list_comp_atr,list_factc)

    matrixCompatibleAtr = normalizeCompatibleAttributes(matrixCompatibleAtr)

    matrixCompatibleAtr.to_pickle(output_path+'matrix_CompatibleAtr_k_'+str(k_attributes)+'_th_'+str(threshold)+'.pkl')    


# In[6]:


def processingSOLID(input_path, output_path, distance_function, correlation, threshold, max_K):
    
    output_path = output_path+'CorDis/'
    
    try:
        # Create target Directory
        os.mkdir(output_path)
    except FileExistsError:
        pass
        
    train_data = pd.read_pickle(input_path+'train_data.pkl')

    ## METHOD OF DISTANCE MAPS #
    matrixValues = generateDistanceMaps(train_data, distance_function, output_path)
    
    ## METHOD OF CORRELATION MAPS #
    matrixCorr = corDiS(matrixValues, correlation, output_path)
    
    for k_attributes in range(1,max_K+1,2):

        ## METHOD OF FIND HIGLY CORRELATED ATTRIBUTES #
        findCompatibleAttributes(train_data, matrixCorr, threshold, k_attributes, output_path, correlation)  


## CoDiS METHO DESCRIPTION
## Fixed Parameters
## Arg1 : Input_path: 'String Format'
## Arg2 : Output_path: 'String Format'
## Arg3 : Distance Function: 'String Format' -> Euclidean, Manhattan and Chebyshev are avaliable
## Arg4 : Correlation Measure: 'String Format' -> Pearson or Spearman are avaliable
## Arg5 :Threshold Correlation: 'Float Format' -> (0,1]
## Arg6 :K_attributes: Integer Format -> Amount of neighboors attributes compatible

## To run python CorDiS.py Arg1 Arg2 Arg3 Arg4 Arg5 Arg6
def main(argv):
    input_path = ''
    output_path = ''
    df = ''
    correlation = ''
    threshold = 0
    k_attributes = 0

    if(len(argv) == 7):
        if(argv[1] is not ''):
            input_path = argv[1]
            
        if(argv[2] is not ''):
            output_path = argv[2]
              
        if(argv[3] is not None):
            df = argv[3]
            
        if(argv[4] is not None):
            correlation = argv[4]

        if(argv[5] is not None):
            threshold = float(argv[5]
                          
        if(argv[6] is not None):
            max_knn = int(argv[6]
        
        processingSOLID(input_path, output_path, distance_function, correlation, max_knn)

    else:
        print('Parameters Not Found!...')
        sys.exit()
    
if __name__ == "__main__": 
    main(sys.argv)

