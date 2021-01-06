import re, os, sys, requests, json, string
from bs4 import BeautifulSoup
from multiprocessing import Pool
import multiprocessing as mp
from collections import defaultdict
from tqdm import tqdm
from pprint import pprint

BASE_DIR = os.path.dirname(__file__)


##### 2.parallel #####
def parallel_crawler(i):
    rt_ex, rt_sent, rt_ng = [], [], []
    url = "https://www.writeexpress.com/" + str(i)
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    for letter in soup.find_all('div','letter mb-4'):
        para = letter.find_all('p')
        para = [str(p) for p in para]
        result = '\n\n'.join([str(re.sub("<.*?>", " ", p)).strip() for p in para])
        rt_ex.append(result)
         
    for example in soup.find_all(class_=re.compile("card (mb-4)$")):
        if len(example.find_all(class_=re.compile("media mb-2"))) > 0:
            sections = example.find_all(class_=re.compile("list-group list-group-flush"))
            sections = [s.find_all(class_=re.compile("list-group-item list-group-item-action")) for s in sections]
            sections = [[re.sub('<.*?>',' ',str(s)).strip() for s in ss] for ss in sections]
            for idx in range(len(sections)):
                for s in sections[idx]:
                    if idx == 0:
                        rt_sent.append(s)
                    else:
                        rt_ng.append(s)
            #print(sections)
            #print()
    return rt_ex, rt_sent, rt_ng


##### 1 #####
def crawl_url():
    print('Start parse categories...')
    url = "https://www.writeexpress.com/"
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    category = {}

    # crawl 63 categories
    for cata in tqdm(soup.find_all('div', {"id": "letter-categories"})):
        for a_cata in soup.find_all('a'):
            result = a_cata.get('href')
            if '/' not in result and '4001letters' not in result and 'recomm01' not in result:
                category[result] = []
    
    # crawl urls in each category
    for cata in tqdm(category.keys()):
        url = "https://www.writeexpress.com/"+ str(cata)
        r = requests.get(url).text
        soup = BeautifulSoup(r, 'html.parser')
        for a in soup.find_all('a', 'list-group-item list-group-item-action'):
            result = a.get('href')
            if '/' not in result:
                category[cata].append(result)

    with open(os.path.join(BASE_DIR,'cat.json'), 'w') as f:
        json.dump(category, f)
    print('Done!')
    return


##### 2 #####
def crawl_content():
    print('Start parallel parse contents...')
    punct = string.punctuation
    category = json.load(open(os.path.join(BASE_DIR, 'cat.json'), 'r'))
    #cat_json = defaultdict(list)
    cat_json = {}
    pool = Pool(mp.cpu_count())
    #for i in link:
    for cat in tqdm(category.keys()):
        urls = category[cat]
        pure_cat = cat.split('.')[0]
        return_value = pool.map(parallel_crawler, urls)
        if len(return_value[0]) != 0 or len(return_value[1]) != 0 or len(return_value[2]) != 0:
            cat_json[pure_cat] = {'example':[], 'sentence':[], 'phrase':[]}
        for rt_ex, rt_sent, rt_ng in return_value:
            rt_ex = [e if e[-1] in punct else e+'.' for e in rt_ex]
            rt_sent = [s if s[-1] in punct else s+'.' for s in rt_sent]
            cat_json[pure_cat]['example'] += rt_ex
            cat_json[pure_cat]['sentence'] += rt_sent
            cat_json[pure_cat]['phrase'] += rt_ng
    pool.close()
    with open(os.path.join(BASE_DIR, 'ex.json'), 'w') as f:
        json.dump(dict(cat_json), f)
    print('Done!')
    return


if __name__ == '__main__':
    if 'crawl_url' in sys.argv[1:]:
        crawl_url()  #Done
    if 'crawl_content' in sys.argv[1:]:
        crawl_content()  #Done
