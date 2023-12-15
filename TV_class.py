import re
from data_cleaning import *
class TV:
    def __init__(self, featuresmap, url, title, shop, modelID):
        self.featuresmap = featuresmap
        self.modelID = modelID
        self.shop = shop
        self.title = title
        self.url = url
        
    def __str__(self):
        return f"Title: {self.title}\nModel ID: {self.modelID}\nShop: {self.shop}\nURL: {self.url}"
            
    def getKeyValue(self, keyWord):
        tv_features = self.getFeatureMap()
        if keyWord in tv_features:
            return tv_features[keyWord]
        else:
            return "NA"

    def getFeatureMap(self):
        return self.featuresmap
            
    def getTitle(self):
        return self.title
    
    def getShop(self):
        return self.shop
    
    def addFeature(self, key, value):
        self.featuresmap[key] = value
        
    def modifyFeatureMap(self,key_toBeMod,modification):
        self.featuresmap[key_toBeMod] = modification
        
    def modifyTitle(self, pattern, substitute):  
        title = self.title
        mod_title = modifyString(pattern, substitute, title)
        self.title = mod_title
        
    def categorizationSize(self, cat_name):
        title = prepTitles([self.title])
        matches = re.finditer(r'(\d{1,2})(\s?)inch', title[0])
    
        screen_size = None
        
        for match in matches:
            screen_size = match.group(1)
            break
        
        categories = [
                (0, 10, '<10"'), (10, 15, '10"-14"'),
                (15, 20, '15"-19"'), (20, 30, '20"-29"'),
                (30, 35, '30"-34"'), (35, 40, '35"-39"'),
                (40, 45, '40"-44"'), (45, 50, '45"-49"'),  
                (50, 55, '50"-54"'), (55, 60, '55"-59"'),
                (60, 65, '60"-64"'), (65, 70, '65"-69"'),
                (70, 75, '70"-74"'), (75, 80, '75"-79"'),
                (80, 90, '80"-89"'), (90, 95, '90"-94"'),
                (95, 100, '95"-99"'),(100, float('inf'), '100"+')]
       
        if screen_size:
            screen_size = int(screen_size)
            for lower_bound, upper_bound, category_name in categories:
                if lower_bound <= screen_size < upper_bound:
                    self.addFeature(cat_name, category_name)
                    return self
            
        if screen_size == None:
            related_keys = findXXXRelatedKeys(self, "size")
            for x in related_keys:
                matches = re.finditer(r'(\d{1,2})(\s?)([\"“”]|\'|inch|in|inches)', x)
    
                for match in matches:
                    screen_size = match.group(1)
                    if screen_size:
                        break
            
                if screen_size:
                    for lower_bound, upper_bound, category_name in categories:
                        if lower_bound <= screen_size < upper_bound:
                            self.addFeature(cat_name, category_name)
                            return self 
                    
        if screen_size == None:
            category = "Unknown"
        self.addFeature(cat_name, category)
        return self

    
    def categorizationRes(self, cat_name):
        title = prepTitles([self.title])
        split_title = title[0].split()
        set_of_res = {"720", "1080", "2160"}
        
        res = [r for r in set_of_res if any(r in word for word in split_title)]        
        if res:
            self.addFeature(cat_name, res[0])
            return self
        
        related_keys = findXXXRelatedKeys(self, "resolution")
        for x in related_keys:
            value = self.featuresmap[x].split()
            res = [r for r in set_of_res if any(r in value for a in value)]
            if res:
                self.addFeature(cat_name, res[0])
                return self
            
        self.addFeature(cat_name, "Unknown")
        return self

    def categorizationRef(self, cat_name):
        title = prepTitles([self.title])
        split_title = title[0].split()
        set_of_ref = {"60hz", "120hz", "240hz", "400hz", "600hz"}
        
        ref = [r for r in set_of_ref if any(r in word for word in split_title)]        
        if ref:
            self.addFeature(cat_name, ref[0])
            return self
        
        related_keys = findXXXRelatedKeys(self, "rate")
        for x in related_keys:
            value = self.featuresmap[x].lower().split()
            ref = [r for r in set_of_ref if any(r in value for a in value)]
            if ref:
                self.addFeature(cat_name, ref[0])
                return self
            
        self.addFeature(cat_name, "Unknown")
        return self
    
    def prepFeaturesSize(self):
        related_sample = findXXXRelatedKeys(self, "size")
        for key in related_sample:
            value = self.featuresmap[key]
            value = re.sub(r'[^\w\s"\']', '', value)
            value = re.sub(r'(\d{3})inch', lambda m: str(round(int(m.group(1)) / 10)) + "inch", value)
            value = re.sub(r'(\d{4})inch', lambda m: str(round(int(m.group(1)) / 100)) + "inch", value)
            value = re.sub(r'\s+', ' ', value).strip()  # Remove extra spaces
            self.modifyFeatureMap(key, value)
        return self
    
    def prepFeaturesRes(self):
        related_sample = findXXXRelatedKeys(self, "resolution")
        for key in related_sample:
            value = self.featuresmap[key]
            value = re.sub(r'[^\w\s"\']', '', value)
            value = re.sub(r'\s+', ' ', value).strip()  # Remove extra spaces
            self.modifyFeatureMap(key, value)
        return self
    
    def prepFeaturesRef(self):
        related_sample = findXXXRelatedKeys(self, "rate")
        for key in related_sample:
            value = self.featuresmap[key]
            value = re.sub(r'[^\w\s\"\']', '', value)
            value = re.sub(r'(\d{1,3})(\s?)(\-hz|hertz|hz)', r'\1hz', value)
            value = re.sub(r'\s+', ' ', value).strip()  # Remove extra spaces
            self.modifyFeatureMap(key, value)
        return self
        
def TVObjectsFromJson(json_data):
    tv_objects = []  # This will store all the TV objects

    # Iterate through each modelID and its list of TVs
    for model_id, tvs in json_data.items():
        for tv in tvs:  # tv_info is a dictionary with the TV information
            # Create a TV object and add it to the list
            tv_objects.append(TV(tv['featuresMap'], tv['url'], tv['title'], tv['shop'], model_id))
    return tv_objects

    
