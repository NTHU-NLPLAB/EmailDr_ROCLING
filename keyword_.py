import re, json, os
from collections import Counter
import numpy as np
from scipy import stats
from nltk import word_tokenize, sent_tokenize
from collections import Counter

REFERENCE_PATH = os.path.join(os.path.dirname(__file__), 'default_reference')
STOPWORD_PATH = os.path.join(os.path.dirname(__file__), 'stopwords')
#collin = json.load(open(COLLINS_PATH, 'r'))
reference = list(map(lambda x: (x.split('\t')[0], int(x.split('\t')[1])), \
                         open(REFERENCE_PATH, 'r').read().strip().split('\n')))
stopwords = set(open(STOPWORD_PATH, 'r').read().strip().split('\n'))

def get_ngram(sections:list, ft):
    count = Counter()
    for sec in sections:
        for sent in sent_tokenize(sec):
            tokens = word_tokenize(sent)
            for n in range(ft[0],ft[-1]+1):
                grams = list(zip(*[tokens[idx:] for idx in range(n)]))
                for ng in grams:
                    cap = [tok[0].isupper() for tok in ng]
                    if not True in cap:
                        count[ng] += 1
    '''for sec in collin[sections[0]:sections[1]+1]:
        for sent in sent_tokenize(sec['content']):
            tokens = word_tokenize(sent)
            for n in range(1,4):
                grams = list(zip(*[tokens[idx:] for idx in range(n)]))
                for ng in grams:
                    count[ng] += 1'''
    return count


def Keyword(sections, ft=[1,2,3], remove_stopwords = True):
    term_chi = []  # chi-square testing
    #sections = [sec.lower() for sec in sections]
    ngram = get_ngram(sections, ft)
    for n in range(ft[0],ft[-1]+1):
        nf = list(filter(lambda x: len(x[0]) == n, ngram.items()))
        # eliminate ngrams with any stopword
        nf = list(filter(lambda x: not any([tok.lower() in stopwords for tok in x[0]]), nf))
        # eliminate pure number
        nf = list(filter(lambda x: all([word.isalpha() for tok in x[0] for word in tok]), nf))
        
        nf = list(map(lambda x: (' '.join(x[0]), x[1]), nf))  # key ngram and freq
        T = Counter(dict(nf))  # T for target file
        R = Counter(dict(list(filter(lambda x: x[0].count(' ')+1 == n, reference))))
        
        #vocab = list(set(T.keys()).union(set(R.keys())))
        total_freq_T = sum(T.values())
        total_freq_R = sum(R.values())
        
        for term in T.keys():
            M = np.array([[T[term], total_freq_T-T[term]], [R[term], total_freq_R-R[term]]])
            chi2, p, dof, ex = stats.chi2_contingency(M, correction=False)
            if round(chi2,3) <= 0.0 or p>0.001:
                continue
            term_chi.append([term, round(chi2,3)])
            #term_chi.append([term, T[term], round(chi2,3), round(p,3)])
        
    term_chi = Counter(dict(sorted(term_chi, key=lambda x: x[1], reverse=True)[:50]))
    #print(json.dumps(term_chi))
    return list(term_chi.keys())

