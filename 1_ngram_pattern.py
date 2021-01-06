import json, spacy
from collections import Counter, defaultdict
from tqdm import tqdm
import multiprocessing as mp
from multiprocessing import Pool


nlp = spacy.load('en')


def get_pos_tag(ngram):
    spacy_ng, is_np = list(zip(*ngram))
    pos_tag = [[(tok, tok.pos_, tok.tag_) for tok in toks] for toks in spacy_ng]
    return pos_tag, is_np
    
    
def get_pattern(tok, pos, tag):
    if pos == 'VERB':
        return 'v.'
    if pos == 'ADV':
        return 'adv.'
    if pos == 'INTJ':
        return 'interj.'
    if pos == 'ADJ':
        return 'adj.'
    if pos == 'NOUN':
        return 'n.'
    if pos == 'PRON':
        return 'SOMEONE'
    if pos == 'PROPN':
        if tok.ent_type_:
            return tok.ent_type_
        else:
            return 'SOMETHING'
    return tok.lemma_ if '-' not in tok.lemma_ else 'SOMEONE'


def make_pattern(ngram, remove_punct = True):
    ng = [[ng.text for ng in ngs] for ngs, _ in ngram]  # pure ngram
    ngram_pos = [[ng.text+'('+ng.pos_+')' for ng in ngs] for ngs, _ in ngram]  # ngram(POS)...
    ngram_pos_tag, is_np = get_pos_tag(ngram)  # pos_tag, is_noun_chunk?1:0
    pos_lists = [p for po_ta in ngram_pos_tag for _, p, _ in po_ta]  # flatten
    if len(ngram_pos_tag) <= 2 or 'PUNCT' in pos_lists: return [], []
    patterns = [ng.copy(), ng.copy()]
    #print(patterns)
    # gen pattern [[token1 pattern...], [token1 token2 pattern...]]
    tok_idx = [[0,0], [0,1] if len(ngram_pos_tag[0]) >= 2 else [1, 0]]
    for now_idx, pat_idx in enumerate(tok_idx):
        # first, transfer remain tokens to pos
        remain_pattern = []
        for tok, p, t in ngram_pos_tag[pat_idx[0]][pat_idx[1]+1:]:
            pt = get_pattern(tok, p, t)
            if len(remain_pattern) == 0 or pt != remain_pattern[-1]:
                remain_pattern.append(pt)
        remain_pattern = ' '.join(ng[pat_idx[0]][:pat_idx[1]+1]+remain_pattern)
        for patterns_idx in range(len(tok_idx)-now_idx):
            patterns[len(tok_idx)-patterns_idx-1][pat_idx[0]] = remain_pattern
        # else
        if ngram_pos_tag[pat_idx[0]+1:] == []: continue
        for idxs, inf in enumerate(ngram_pos_tag[pat_idx[0]+1:]):
            tok, p, t = list(zip(*inf))
            idx = idxs + pat_idx[0] + 1
            if is_np[idx] == 1:
                if len(p) == 1 and p[0] == 'PRON':
                    patterns[now_idx][idx] = 'SOMEONE'
                else:
                    ents = [tk.ent_type_ for tk in tok if tk.ent_type_ != '']
                    ent = '' if ents == [] else max(ents, key=lambda x: ents.count(x))
                    if ent == '':
                        patterns[now_idx][idx] = 'n.'
                    else:
                        patterns[now_idx][idx] = ent
            else:
                patterns[now_idx][idx] = get_pattern(tok[0], p[0], t[0])
    #print(list(set([tuple(p) for p in patterns])), [' '.join(ng) for ng in ngram_pos], flush=True)
    return list(set([tuple(p) for p in patterns])), [' '.join(ng) for ng in ngram_pos]


def parse_spacy(sent):
    return nlp(sent)


def ngram_pattern(data, ft, target_path, lower=False, lemma=False):
    pool = Pool()
    ng_pt = {}
    # go through different keys
    for c in data.keys():
        print('['+c+']')
        ng_pt[c] = defaultdict(Counter)
        #ng_pt[c] = {'example': defaultdict(Counter), 'sentence':defaultdict(Counter), 'phrase':defaultdict(Counter)}
        # go through ['example', 'sentence', 'phrase']
        for t, sents in data[c].items():
            print('['+t+']')
            print('-> Parse Spacy Information...')
            #docs = pool.map(parse_spacy, tqdm(sents))  # get all paragraph's spacy
            docs = []
            for s in sents:
                docs.append(parse_spacy(s))
            # retrieve each paragraph
            print('->split ngram and get pattern...')
            for doc in tqdm(docs):
                for sent in doc.sents:
                    # combine noun_chunks to one elements
                    np = list(sent.noun_chunks)
                    np_str_idx, np_end_idx = list(zip(*[(n[0].i, n[-1].i+1) for n in np])) if len(np)>0 else ([], [])
                    np_sent = []
                    tok_idx = sent[0].i
                    while tok_idx <= sent[-1].i:
                        if tok_idx in np_str_idx:
                            np_idx = np_str_idx.index(tok_idx)
                            np_sent.append([doc[np_str_idx[np_idx]: np_end_idx[np_idx]], 1])
                            tok_idx = np_end_idx[np_idx]
                        else:
                            np_sent.append([doc[tok_idx:tok_idx+1], 0])
                            tok_idx += 1
                    if t != 'phrase':
                        # extract ngrams
                        for n in ft:
                            ngrams = list(zip(*[np_sent[i:] for i in range(n)]))
                            # ngrams: [([tok1, 1/0],[tok2, 1/0]...), (...)...]
                            for ngram in ngrams:
                                pts, ng = make_pattern(ngram)
                                for pt in pts:
                                    ng_pt[c][' '.join(pt)][' '.join(ng)] += 1
                                    #ng_pt[c][t][' '.join(pt)][' '.join(ng)] += 1
                    else:
                        pts, ng = make_pattern(np_sent)
                        for pt in pts:
                            ng_pt[c][' '.join(pt)][' '.join(ng)] += 1
        print()
    #pool.close()
    #pool.join()
    json.dump(ng_pt, open(target_path, 'w'))


if __name__ == '__main__':
    d = json.load(open('ex.json'))
    ft = [3,4,5]
    rt = ngram_pattern(d, ft, 'ngram_pattern.json')
    