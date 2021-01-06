import json, re
from nltk import word_tokenize
from collections import defaultdict, Counter
from tqdm import tqdm

stopwords = open('stopwords', 'r').read().strip().split('\n')
ngram = json.load(open('ngram_pattern.json', 'r'))
synonyms = json.load(open('synonyms.json', 'r'))
collos = json.load(open('collocations.json' ,'r'))
collo = defaultdict(lambda: defaultdict(Counter))
# transfer colloctions' type
for dist, els in collos.items():
    for l_tok, els2 in els.items():
        for r_tok, count in els2.items():
            collo[int(dist)][l_tok][r_tok] = count
            

def get_skgm(ng, n = 5):
    skgm = defaultdict(lambda: defaultdict(lambda: 0))
    tokens = word_tokenize(ng)
    for idx1 in range(len(tokens)-1):
        for idx2 in range(idx1+1, min(len(tokens), idx1+n)):
            dist = idx2-idx1
            skgm[tokens[idx1]][tokens[idx2]] = dist
    return skgm


def filter_lbs():
    clear_ngram = defaultdict(lambda: defaultdict(Counter))
    for k in tqdm(ngram.keys()):
        synset = synonyms[k]
        for pat in ngram[k].keys():
            for ng, count in ngram[k][pat].items():
                first_pos = re.findall('\([A-Z]+\)', ng)[0][1:-1]
                if first_pos == 'PROPN': continue
                clear_ng = re.sub('\([A-Z]+\)', '', ng)
                skgm = get_skgm(clear_ng)
                score = 0
                for l_tok, els in skgm.items():
                    for r_tok, dist in els.items():
                        if l_tok.lower() in stopwords or r_tok.lower() in stopwords:
                            score += collo[dist][l_tok][r_tok]
                if score > 0:
                    clear_ngram[k][pat][ng] = count
                    # GET SYNONYMS
                    pure_ng = re.sub('\([A-Z]+\)', '', ng).split()
                    pure_pos = re.findall('\([A-Z]+\)', ng)
                    pure_pt = pat.split()
                    for l, r, _ in synset:
                        if l in pure_ng and l in pure_pt:
                            pure_ng[pure_ng.index(l)] = r
                            pure_pt[pure_pt.index(l)] = r
                            ng_pos = [pure_ng[idx]+pure_pos[idx] for idx in range(len(pure_ng))]
                            clear_ngram[k][' '.join(pure_pt)][' '.join(ng_pos)] += clear_ngram[k][pat][ng]
                        elif l in pure_ng:
                            pure_ng[pure_ng.index(l)] = r
                            ng_pos = [pure_ng[idx]+pure_pos[idx] for idx in range(len(pure_ng))]
                            clear_ngram[k][pat][' '.join(ng_pos)] += clear_ngram[k][pat][ng]
                        elif r in pure_ng and r in pure_pt:
                            pure_ng[pure_ng.index(r)] = l
                            pure_pt[pure_pt.index(r)] = l
                            ng_pos = [pure_ng[idx]+pure_pos[idx] for idx in range(len(pure_ng))]
                            clear_ngram[k][' '.join(pure_pt)][' '.join(ng_pos)] += clear_ngram[k][pat][ng]
                        elif r in pure_ng:
                            pure_ng[pure_ng.index(r)] = l
                            ng_pos = [pure_ng[idx]+pure_pos[idx] for idx in range(len(pure_ng))]
                            clear_ngram[k][pat][' '.join(ng_pos)] += clear_ngram[k][pat][ng]
                            
    json.dump(clear_ngram, open('LBS_pattern.json', 'w'))
    

if __name__ == '__main__':
    filter_lbs()