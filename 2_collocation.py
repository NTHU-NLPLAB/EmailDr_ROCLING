import pandas as pd
from nltk import sent_tokenize, word_tokenize
import re, json, os
from collections import Counter, defaultdict
from tqdm import tqdm
import numpy as np
from math import sqrt


BASE_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(BASE_DIR, FILE_PATH)

df = pd.read_csv(FILE_PATH)


def count_collocations(data, n):
    skgm = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
    for email in tqdm(data):  #['ngram']
        for sent in sent_tokenize(email):
            tokens = word_tokenize(sent)
            for idx1 in range(len(tokens)-1):
                if not re.search('[a-zA-Z]', tokens[idx1]):
                    continue
                for idx2 in range(idx1+1, min(idx1+n, len(tokens))):
                    if not re.search('[a-zA-Z]', tokens[idx2]):
                        continue
                    distance = idx2-idx1
                    skgm[tokens[idx1]][tokens[idx2]][distance] += 1
                    skgm[tokens[idx2]][tokens[idx1]][-distance] += 1
    return skgm


def calculate_collocations(skgm):
    skipbigram_static = defaultdict(lambda: defaultdict())
    for pro, tag_list in tqdm(skgm.items()):
        W = [sum(skgm[pro][tag].values()) for tag in tag_list]
        f = np.average(W)
        standard_deviation = np.std(W) + 1e-10

        for tag in tag_list:
            data = skgm[pro][tag].values()

            freq = sum(data)
            avg_p = sum([a*b for a, b in skgm[pro][tag].items()])/freq

            pos_spread = sum(map(lambda x: (x - avg_p)**2, data))/10
            strength = (freq - f)/standard_deviation

            skipbigram_static[pro][tag] = {
                'freq':freq, 
                'avg_p':avg_p, 
                'pos_spread':pos_spread, 
                'strength':strength}

    return skipbigram_static


def filter_collocations(skgm, skipbigram_static):
    # valid_collocations = defaultdict(lambda: defaultdict(list))
    K0 = 1
    U0 = 5
    K1 = 1
    output = []
    for key, tag_list in tqdm(skgm.items()):
        for tag, values in tag_list.items():
            data = skipbigram_static[key][tag]
            if data['strength'] >= K0 and data['pos_spread'] >= U0:
                for value in values.items():
                    if value[1] >= data['avg_p'] + (K1*sqrt(data['pos_spread'])):
                        # valid_collocations[key][tag].append(value)
                        output.append([key, tag, value[0], value[1]])
                        
    output = sorted(output, key = lambda x: x[3], reverse=True)
    output_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda:0)))
    for l, r, d, c in output:
        if d > 0:
            output_dict[d][l][r] = c
                        
    return output_dict


def Collocation(data):
    skgm = count_collocations(data, 5)
    skipbigram_static = calculate_collocations(skgm)
    output = filter_collocations(skgm, skipbigram_static)
    #print(json.dumps(output))
    json.dump(output, open('collocations.json','w'))
    return 


def run():
    data = ['\n'.join(msg.split('X-FileName:')[1].split('\n')[1:]).strip() for msg in df['message']]    
    Collocation(data)

run()