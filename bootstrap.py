import json
import time
import random
import re
from collections import defaultdict
from functools import reduce

from TV_class import *
from shingling import *
from MinHash import *
from linkage_clustering import *
from itertools import combinations
from data_cleaning import*


def trueDup(tv_list):
    true_duplicates = set()
    for tv1, tv2 in combinations(tv_list, 2):
        if tv1.modelID == tv2.modelID:         
            true_duplicates.add((tv1, tv2))
    return true_duplicates

def bootStrap(tv_list, num_ofBags, full_samp = False):
    bootstrap_dict = {}
    bootstrap_dup_dict = {}
    if full_samp:
        for i in range(num_ofBags):
            bootstrap_dict[i] = (tv_list, [])
            trueDup_s = trueDup(tv_list)
            bootstrap_dup_dict = {i: (trueDup_s, [])}
    else:
        for i in range(num_ofBags):
            indices = {random.randint(0, len(tv_list) - 1) for i in range(len(tv_list))}
            complement_indices = set(range(len(tv_list))) - set(indices)

            bootstrap_samples = [tv_list[i] for i in indices]
            trueDup_s = trueDup(bootstrap_samples)
            bootstrap_complements = [tv_list[i] for i in complement_indices]
            trueDup_c = trueDup(bootstrap_complements)

            bootstrap_dict[i] = (bootstrap_samples, bootstrap_complements)
            bootstrap_dup_dict[i] = (trueDup_s, trueDup_c)
    
    return bootstrap_dict, bootstrap_dup_dict

def getTitlesBoot(bootstrap_dict):
    bootstrap_title_dict = {}
    for key, (sample_list, complement_list) in bootstrap_dict.items():
        title_list_samp = [tv.title for tv in sample_list]
        title_list_comp = [tv.title for tv in complement_list]
        bootstrap_title_dict[key] = (title_list_samp, title_list_comp)
    return bootstrap_title_dict
    
def titlesToMwBoot(bootstrap_dict):  
    boot_title_dict = getTitlesBoot(bootstrap_dict)
    boot_mwTitle_dict = {}
    for key, (sample_list, complement_list) in boot_title_dict.items():
        mw_sample_list = commonMwTitles(sample_list)
        mw_complement_list = commonMwTitles(complement_list)
        
        mw_sample_list = {i for i,j in mw_sample_list}
        mw_complement_list = {i for i,j in mw_complement_list}
        #filter
        set_of_res = {"720", "1080", "2160"}
        mw_sample_list = {mw for mw in mw_sample_list if len(mw) > 2 
                          and any(char.isdigit() for char in mw) 
                          and not all(char.isdigit() for char in mw)
                          and "inch" not in mw and "hz" not in mw 
                          and all(r not in mw for r in set_of_res)}
                               
        mw_complement_list = {mw for mw in mw_complement_list if len(mw) > 2 and 
                              any(char.isdigit() for char in mw) and not all(char.isdigit() for char in mw) 
                              and "inch" not in mw and "hz" not in mw and
                              all(r not in mw for r in set_of_res)} 
        
        boot_mwTitle_dict[key] = (mw_sample_list,mw_complement_list)
    return boot_mwTitle_dict

def getBrandMwBoot(bootstrap_dict):
    boot_mwbrand_dict = {}
    for key, (sample_list, complement_list) in bootstrap_dict.items():
        brand_keyMap_s, brand_keyMap_List_s = findXXXRelatedKeysList(sample_list, "brand")
        brand_keyMap_c, brand_keyMap_List_c = findXXXRelatedKeysList(complement_list, "brand")
        
        mw_brand_s = {brand.lower() for key, brand in brand_keyMap_List_s }
        mw_brand_c = {brand.lower() for key, brand in brand_keyMap_List_c }
        #filter
        mw_brand_s = {mw for mw in mw_brand_s if mw not in {"pansonic" ,"hello kitty", "jvc tv", "lg electronics", "sceptre inc."} }
        mw_brand_c = {mw for mw in mw_brand_c if mw not in {"pansonic" ,"hello kitty", "jvc tv", "lg electronics", "sceptre inc."} }
        
        boot_mwbrand_dict[key] = (mw_brand_s, mw_brand_c)
    return boot_mwbrand_dict

def sizeMwCatBoot(bootstrap_dict):
    new_bootstrap_dict = {}
    for key, (sample_list, complement_list) in bootstrap_dict.items():
        sample_list = [tv.prepFeaturesSize() for tv in sample_list]
        sample_list = [tv.categorizationSize("LSH size") for tv in sample_list]
        complement_list = [tv.prepFeaturesSize() for tv in complement_list]
        complement_list = [tv.categorizationSize("LSH size") for tv in complement_list]

        new_bootstrap_dict[key] = (sample_list, complement_list)
    
    return new_bootstrap_dict

def resMwCatBoot(bootstrap_dict):
    new_bootstrap_dict = {}
    for key, (sample_list, complement_list) in bootstrap_dict.items():
        sample_list = [tv.prepFeaturesRes() for tv in sample_list]
        sample_list = [tv.categorizationRes("LSH res") for tv in sample_list]
        complement_list = [tv.prepFeaturesRes() for tv in complement_list]
        complement_list = [tv.categorizationRes("LSH res") for tv in complement_list]

        new_bootstrap_dict[key] = (sample_list, complement_list)
    return new_bootstrap_dict

def refMwCatBoot(bootstrap_dict):
    new_bootstrap_dict = {}
    for key, (sample_list, complement_list) in bootstrap_dict.items():
        sample_list = [tv.prepFeaturesRef() for tv in sample_list]
        sample_list = [tv.categorizationRef("LSH rate") for tv in sample_list]
        complement_list = [tv.prepFeaturesRef() for tv in complement_list]
        complement_list = [tv.categorizationRef("LSH rate") for tv in complement_list]

        new_bootstrap_dict[key] = (sample_list, complement_list)
    return new_bootstrap_dict
    
def LSHandClus(bootstrap_dict, bootstrap_dup_dict ,num_hash):
    def tp_fp(candidates,tv_list):
        tp = set()
        fp = set()

        for a, b in candidates:

            tv1 = tv_list[a]
            tv2 = tv_list[b]

            if tv1.modelID == tv2.modelID:
                tp.add((a,b))
            else:
                fp.add((a,b))

        return tp, fp

        
    mw_title_dict = titlesToMwBoot(bootstrap_dict)
    mw_brand_dict = getBrandMwBoot(bootstrap_dict)
    titles_dict = getTitlesBoot(bootstrap_dict)
    
    tp_fp_LSH = []
    tp_fp_clustering = []
    metrics_LSH = []
    metrics_clustering = []
    metrics_gen = []
    for i in range(len(bootstrap_dict)):
        print("start MSH")
        start = time.time()

        mw_title = mw_title_dict[i][0]
        mw_brand = mw_brand_dict[i][0]
        mw_size = {
            ('<10"'), ('10"-14"'),
            ('15"-19"'), ('20"-29"'),
            ('30"-34"'), ('35"-39"'),
            ('40"-44"'), ('45"-49"'),  
            ('50"-54"'), ('55"-59"'),
            ('60"-64"'), ('65"-69"'),
            ('70"-74"'), ('75"-79"'),
            ('80"-89"'), ('90"-94"'),
            ('95"-99"'),('100"+')}
        mw_res = {'720', '1080', '2160'}
        mw_ref = {"60hz", "120hz", "240hz", "600hz"}

        temp_tv_list = bootstrap_dict[i][0]
        titles = titles_dict[i][0]
        titles_clean = prepTitles(titles)
        mw_merged = mw_title | mw_brand | mw_size |mw_res | mw_ref
        
        # bm_shin         = binaryMatrixShingledTitles(titles_clean,5)
        bm_clean_title  = binaryMatrixCleanedTitle(titles_clean, mw_title)
        bm_brand        = binaryMatrixCleanedTitle(titles_clean, mw_brand)
        bm_size         = binaryMatrixSize(temp_tv_list, mw_size)
        bm_res          = binaryMatrixRes(temp_tv_list, mw_res)
        bm_ref          = binaryMatrixRef(temp_tv_list,mw_ref)   
        bm = np.vstack((bm_clean_title, bm_brand, bm_size,bm_brand,bm_res,bm_ref)) 
        print("bm check: ", bmCheck(bm), "bm shape: ", bm.shape)
        MHS = minHashSignatures(bm, num_hash)
        
        metrics_gen.append(len(bootstrap_dup_dict[i][0]))

        end = time.time()
        print(f"Time taken: {end - start} seconds")
        
        factors = bandRow(num_hash)
        for j in range(len(factors)): 
        ### LSH part
            b, r = factors[j]
            print(f"b = {b}, r = {r}")
            print("start LSH")
            start = time.time()
            
            candidates = identicalBandsLSH(MHS,b,r)  
            
            tp_LSH, fp_LSH = tp_fp(candidates, temp_tv_list)
            
            PQ_s = len(tp_LSH) / len(candidates)
            PC_s = len(tp_LSH) / len(bootstrap_dup_dict[i][0])
            if PQ_s + PC_s != 0:
                F1_s = (2 * PQ_s * PC_s) / (PQ_s + PC_s)
            else:
                F1_s = 0  
            fc_LSH = len(candidates)/ (len(bootstrap_dict[i][0]) * (len(bootstrap_dict[i][0]) - 1) / 2)
            
            tp_fp_LSH.append((len(tp_LSH), len(fp_LSH), i, b, r))
            metrics_LSH.append((PQ_s, PC_s, F1_s, fc_LSH,i,b,r))
        
            end = time.time()
            print(f"Time taken: {end - start} seconds")
        ### clustering part
            print("start clustering")
            start = time.time()
        
            duplicates = set()
            for c, d in candidates:
                tv1 = temp_tv_list[c]
                tv2 = temp_tv_list[d]
                sim = jaccardSimilarity(tv1, tv2, mw_merged)
                if sim >= 0.5:
                    duplicates.add((c,d))
    
            tp_r, fp_r = tp_fp(duplicates, temp_tv_list)
    
            PQ = len(tp_r) / len(duplicates)
            PC = len(tp_r) / len(bootstrap_dup_dict[i][0])
            if PQ + PC != 0:
                F1 = (2 * PQ * PC) / (PQ + PC)
            else:
                F1 = 0 
            fcc =  len(duplicates) / (len(bootstrap_dict[i]) * (len(bootstrap_dict[i][0]) - 1) / 2)
        
            tp_fp_clustering.append((len(tp_r), len(fp_r), i,b,r))
            metrics_clustering.append((PQ, PC, F1, fcc, i,b,r))
            metrics_gen.append((len(candidates),len(duplicates), i, b ,r))

            end = time.time()
            print(f"Time taken: {end - start} seconds, bootstrap number: {i}")
    return  tp_fp_LSH, metrics_LSH, tp_fp_clustering, metrics_clustering


