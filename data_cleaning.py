import re
from collections import Counter
import TV_class
# data cleaning
def prepTitles(titles):
    cleaned_titles = []
    for title in titles:
        title = title.lower()  # Convert to lower case
        title = re.sub(r'[^\w\s\"\']', '', title)   # Remove special characters
        
        title = re.sub(r'(\d{4})(\s?)([\"“”]|\'|inch|in)', lambda m: f"{round(int(m.group(1)) / 100)}inch", title)
        title = re.sub(r'(\d{3})(\s?)([\"“”]|\'|inch|in)', lambda m: f"{round(int(m.group(1)) / 10)}inch", title)

        title = re.sub(r'(\d{1,2})(\s?)([\"“”]|\'|inch|in)', r'\1inch', title)

        title = re.sub(r'(\d{1,3})(\s?)(\-hz|hertz|hz)', r'\1hz', title)

        title = re.sub(r'\s+', ' ', title).strip()  # Remove extra spaces
        cleaned_titles.append(title)
    return cleaned_titles

def mwTitles(titles):
    mws = []
    for title in titles:
        mws.extend(title.split())
    return mws

def commonMwTitles(titles):
    cleaned_titles = prepTitles(titles)
    mws = mwTitles(cleaned_titles)
    frequency = Counter(mws)
    return frequency.most_common()

def sortOnWebsite(tv_list):
    neweggTVs = []
    amazonTVs = []
    bestBuyTVs = [] 
    computerNerdsTVs = []

    for tv in tv_list:
        if(tv.shop == "newegg.com"):
            neweggTVs.append(tv)
        if(tv.shop == "amazon.com"):
            amazonTVs.append(tv)
        if(tv.shop == "bestbuy.com"):
            bestBuyTVs.append(tv)
        if(tv.shop == "thenerds.net"):
            computerNerdsTVs.append(tv)
    return neweggTVs, amazonTVs, bestBuyTVs, computerNerdsTVs

# featuremap analysis && key selection and standardizatio
def countFeatureKeys(tv_list):
    #overall key count
    key_counts = {}
    for tv in tv_list:
        features = tv.featuresmap
        # overall key counter
        for key in features:
            if key in key_counts:
                key_counts[key] += 1
            else:
                key_counts[key] = 1
    #key count per website
    website_key_counts = {}
    for tv in tv_list:
        shop = tv.shop
        features = tv.featuresmap
        if shop not in website_key_counts:
            website_key_counts[shop] = {}
        for key in features:
            website_key_counts[shop].setdefault(key, 0)
            website_key_counts[shop][key] += 1
    return key_counts, website_key_counts

def findXXXRelatedKeysList(tv_list, string):
    key_map = {}
    key_map_list = []  
    for tv in tv_list:
        shop = tv.shop
        features = tv.featuresmap
        xxx_related = {key for key in features if string in key.lower()}
        
        if shop not in key_map:
            key_map[shop] = {}
        
        for i, value in enumerate(xxx_related):
            key_map[shop][value] = features[value]
            key_map_list.append((value, features[value]))
            
    return key_map, key_map_list

def findXXXRelatedKeys(tv, string):
    features = tv.featuresmap
    return [key for key in features if string in key.lower()]

def removeKeysContainingString(list_removal, string):    
    return [(i1,i2) for i1, i2 in list_removal if string not in i1.lower()]

def modifyString(pattern, substitute, string):
    return re.sub(pattern,substitute, string)      

