import numpy as np
import sympy
import math
import re
import data_cleaning
from linkage_clustering import shingleSet
from functools import reduce
def binaryMatrixCleanedTitle(clean_title_list, modelwords):
    bm = np.zeros((len(modelwords), len(clean_title_list)),dtype = int)
    mw_i = {mw : index for index, mw in enumerate(modelwords)}
    for j, title in enumerate(clean_title_list):
        split_title = set(title.split())
        mw_inTitle = modelwords.intersection(split_title)
        for modelword in mw_inTitle:
            i = mw_i[modelword]
            bm[i,j] = 1
    return bm 

def binaryMatrixSize(tv_list, modelwords):
    product_matrix = np.zeros((len(modelwords),len(tv_list)))
    mw_i = {mw : index for index, mw in enumerate(modelwords)}

    for j, tv in enumerate(tv_list):
        features = tv.featuresmap
        if features["LSH size"] == "Unknown":
            continue
        if "LSH size" in features:
            value = features["LSH size"]
            i = mw_i[value]
            product_matrix[i,j] = 1
    return product_matrix

def binaryMatrixRes(tv_list, modelwords):
    product_matrix = np.zeros((len(modelwords),len(tv_list)))
    mw_i = {mw : index for index, mw in enumerate(modelwords)}

    for j, tv in enumerate(tv_list):
        features = tv.featuresmap
        if features["LSH res"] == "Unknown":
            continue
        if "LSH res" in features:
            value = features["LSH res"]
            i = mw_i[value]
            product_matrix[i,j] = 1
    return product_matrix

def binaryMatrixRef(tv_list, modelwords):
    product_matrix = np.zeros((len(modelwords),len(tv_list)))
    mw_i = {mw : index for index, mw in enumerate(modelwords)}

    for j, tv in enumerate(tv_list):
        features = tv.featuresmap
        if features["LSH rate"] == "Unknown":
            continue
        if "LSH rate" in features:
            value = features["LSH rate"]
            i = mw_i[value]
            product_matrix[i,j] = 1
    return product_matrix


def binaryMatrixShingledTitles(cleaned_titles, k):
    shop_names = {"neweggcom", "best buy", "thenerdsnet"}
    contamination = {"diag", "diagonal", "with", "hospitiality", "natural", "thx", "bundle",
                     "brushed", "display", "combo", "class", "hdiag", "refurbished", "tvs", "of", "169", "active"
                     , "measured"}    
    cleaned_titles = [reduce(lambda t, shop: t.replace(shop, ""), shop_names, title) for title in cleaned_titles]
    cleaned_titles = [reduce(lambda t, cont: t.replace(cont, ""), contamination, title) for title in cleaned_titles]

    cleaned_titles = [title.replace(" ", "") for title in cleaned_titles]
    
    all_shingles = set()
    for title in cleaned_titles:
        all_shingles.update(shingleSet(title, k))
    
    shingle_i = {shingle: index for index, shingle in enumerate(all_shingles)}
    
    bm = np.zeros((len(all_shingles), len(cleaned_titles)), dtype=int)
    for j, title in enumerate(cleaned_titles):
        title_shingles = shingleSet(title, k)
        for shingle in title_shingles:
            i = shingle_i[shingle]
            bm[i, j] = 1
    return bm

def bmCheck(bm):
    cr = 0
    cc = 0
    nrows, ncols = bm.shape
    for i in range(nrows):
        if sum(bm[i]) == 0:
            cr += 1
    for j in range(ncols):
        if sum(bm[:,j]) == 0:
            cc += 1
    return cr, cc
   
def minHashSignatures(binaryMatrix, num_hash):
    num_rows, num_cols = binaryMatrix.shape
    
    signatures = np.full((num_hash, num_cols), np.inf)
    modulus_prime = sympy.nextprime(num_cols)

    a = np.random.randint(1, modulus_prime, num_hash).reshape(num_hash, 1)
    b = np.random.randint(0, modulus_prime, num_hash).reshape(num_hash, 1)

    row_indices = np.arange(num_rows).reshape(1, num_rows)
    hash_vals = (a * row_indices + b) % modulus_prime
    for r in range(num_rows):
        non_zero_cols = binaryMatrix[r, :] > 0
        signatures[:, non_zero_cols] = np.minimum(signatures[:, non_zero_cols], hash_vals[:, r].reshape(-1, 1))

    signatures = signatures.astype(int)
    return signatures

def identicalBandsLSH(minHashSignatures, b,r):
    #preparation
    num_rows, num_cols = minHashSignatures.shape
    reshaped_matrix = minHashSignatures.reshape(b, r, num_cols)
    resultMat = np.zeros((b,num_cols))
     
    def bandHash(band):
        prime = 101
        num_buckets = sympy.nextprime(num_cols)
        indices = np.arange(band.shape[0])
        hash_values = (band + indices[:, None]) * (prime ** indices[:, None] % num_buckets)
        return np.sum(hash_values, axis=0) % num_buckets
    
    candidates = set()
    for band_index in range(b):
       band = reshaped_matrix[band_index, :, :]
       hash_values = bandHash(band)

       # Group columns by hash value
       hash_groups = {}
       for col_index, hash_val in enumerate(hash_values):
           hash_groups.setdefault(hash_val, []).append(col_index)

       # Generate candidates from groups
       for group in hash_groups.values():
           for i in range(len(group)):
               for j in range(i + 1, len(group)):
                   candidates.add((group[i], group[j]))
    
    candidates = {tuple(sorted(tup)) for tup in candidates}
    return candidates

def jaccardSimilarity(tv1, tv2, modelwords):
    if tv1.shop == tv2.shop:
        return 0.0
    # if tv1.featuresmap["LSH size"] == tv2.featuresmap["LSH size"]:
    #     return 0.0

    title1 = data_cleaning.prepTitles([tv1.title])
    title2 = data_cleaning.prepTitles([tv2.title])
    
    title1 = set(title1[0].split())
    title2 = set(title2[0].split())
    
    t1_mw = modelwords.intersection(title1)
    t2_mw = modelwords.intersection(title2)
  
    inter_mw = t1_mw.intersection(t2_mw)
    union_mw = t1_mw.union(t2_mw)
    if not union_mw:
        return 0.0  # Avoid division by zero if both titles are empty
    similarity_mw = len(inter_mw) / len(union_mw)
    return similarity_mw

def bandRow(n_rows):
    factors = []
    for i in range(1, n_rows + 1):
        if n_rows % i == 0:
            factors.append((i, n_rows // i))
    return factors









