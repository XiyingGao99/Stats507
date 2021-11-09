#!/usr/bin/env python
# coding: utf-8

# # Homework 2
# *Xiying Gao(xiying@umich.edu)*
# *Sep 17, 2021*

# In[2]:


import numpy as np
import pandas as pd
import re
from timeit import Timer
from collections import defaultdict
from IPython.core.display import display, Markdown


# ## Question 3

# ### a.

# In[41]:


def data_year(data_suffix):
    """
    use the suffix in the name of the dataset to determine its year.

    Parameters
    ----------
    data_suffix : STR
        THE SUFFIX IN THE NAME OF THE DATASET.

    Returns
    -------
    str
        THE YEAR COHORT.

    """
    
    if data_suffix == "G":
        return "2011-2012"
    if data_suffix == "H":
        return "2013-2014"
    if data_suffix == "I":
        return "2015-2016"
    if data_suffix == "J":
        return "2017-2018"
    
    
demo_df = pd.DataFrame()

# read from the website
url_main = "https://wwwn.cdc.gov/Nchs/Nhanes/"

for data_suffix in ["G", "H", "I", "J"]:
    demo_url = url_main + data_year(data_suffix) + "/DEMO_" + data_suffix + ".XPT"
    demo_dataset = pd.read_sas(demo_url)
    
    #keep some columns
    demo_dataset = demo_dataset[['SEQN', 'RIDAGEYR', 'RIDRETH3', 'DMDEDUC2',
             'DMDMARTL','RIDSTATR', 'SDMVPSU', 'SDMVSTRA', 'WTMEC2YR', 
             'WTINT2YR']]
    
    #rename columns
    demo_dataset.columns = ['id', 'age', 'race_ethnicity', 'education',
                            'marital_status', 'interview_status', 'sdmv_psu', 
                            'sdmv_stra', 'wt_mec_2yr', 'wt_interview_2yr']
    
    #Add an identifying column 
    demo_dataset['cohort_year'] = data_year(data_suffix)
    
    #solve missing values and convert columns' type
    for column in demo_dataset.columns:
        demo_dataset[column] = demo_dataset[column].fillna(-1)
        if column not in ['wt_mec_2yr', 'wt_interview_2yr', 'cohort_year']:
            demo_dataset[column] = demo_dataset[column].astype(int)
            
    #merge into the final database using successive index
    demo_df = pd.concat([demo_df,demo_dataset], ignore_index=True)

#save the resulting data frame using pickle format
demo_df.to_pickle("./demo.pkl")


# ### b.

# In[42]:


dent_df = pd.DataFrame()

for data_suffix in ["G", "H", "I", "J"]:
    dent_url = url_main + data_year(data_suffix) + "/OHXDEN_" + data_suffix + ".XPT"
    dent_dataset = pd.read_sas(dent_url)
    
    #keep some columns
    keeping_col = ['SEQN', 'OHDDESTS']
    
    for column in dent_dataset.columns:
        new_name = "new"
        # find columns, rename columns, and convert columns' type
        if re.findall(r'OHX\d+TC', column) != []:
            new_name = "tooth_counts_" + re.findall(r'OHX(\d+)TC', column)[0]
            dent_dataset[column] = dent_dataset[column].fillna(-1)
            dent_dataset[column] = dent_dataset[column].astype(int)
        elif re.findall(r'OHX\d+CTC', column) != []:
            new_name = "coronal_cavities_" + re.findall(r'OHX(\d+)CTC', 
                                                        column)[0]
            dent_dataset[column] = dent_dataset[column].fillna(-1)
        if new_name != "new":
            dent_dataset.rename(columns={column: new_name}, inplace=True)
            keeping_col.append(new_name)
    
    dent_dataset = dent_dataset[keeping_col]
            
    dent_dataset.rename(columns={"SEQN":"id", "OHDDESTS":"dentition_status"}, 
                        inplace=True)
    dent_dataset = dent_dataset.astype({'id': 'int', 
                                        'dentition_status': 'int'})
    
    
    dent_df = pd.concat([dent_df,dent_dataset], ignore_index=True)

dent_df.to_pickle("./dent.pkl")


# ### c.

# In[44]:


sum_table = {'Demographic Dataset': demo_df.shape[0],
             'Oral Health and Dentition Dataset': dent_df.shape[0]}
sum_table_df = pd.DataFrame(sum_table, index = ['case number'])
display(Markdown(sum_table_df.to_markdown(index=True)))

# edit from PS4Q1
path = './'
demo_file = path + '/demo.feather'
demo = pd.read_feather(demo_file)
ohx_file = path + '/ohx.feather'
ohx = pd.read_feather(ohx_file)
demo.head()

# merge
demo = pd.merge(demo, ohx[['id', 'dentition_status']], on=['id'], how='left')
demo.rename(columns={'dentition_status': 'ohx_status'}, inplace = True)

# generate new variables
demo['under_20'] = np.where((demo['age'] < 20), True, False)

demo['college'] = np.where((demo['education'] == 'Some college or AA degree')|
                          (demo['education'] == 'College graduate or above'), 
                           True, False)

demo['ohx'] = np.where((demo['exam_status'] == 
                        'Both interviewed and MEC examined')&
                       (demo['ohx_status'] == 'Complete'), 
                       True, False)

keep_col = ['id', 'gender', 'age', 'under_20', 'college', 
            'exam_status', 'ohx_status', 'ohx']
demo = demo[keep_col]

demo_cat = {
    'under_20': {True: 'age < 20', False: 'age >= 20'},
    'college': {True: 'some college/college graduate',
                False: 'No college/<20'},
    'ohx': {True: 'complete', False: 'missing'}
}

for col, d in demo_cat.items():
    demo[col] = pd.Categorical(demo[col].replace(d))

