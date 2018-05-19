import json
import numpy as n
import snowballstemmer as sn

def tagger(input_text):
    tags=[]
    def sigmoid(x):
        return 1/(1+n.exp(-1*x))

    stop_list = 'но и с от по над в об у'.split()
    stemmer = sn.RussianStemmer()

    #загружаем результат обучения
    synapse_file = 'synapses.json'
    with open(synapse_file) as data_file:
        synapse = json.load(data_file)
        W_1 = n.asarray(synapse['W_1'])
        W_2 = n.asarray(synapse['W_2'])
        clean_st = synapse['clean_st']
    try:
        Z=[]
        tests = [input_text]
        for i in tests:
            #print('текст: ',i)
            b=[1]# *тут первые единицы для W_1_0 нужны
            i=i.lower()
            a = i.split()
            for word in a:
                if word in stop_list:
                    a.remove(word)
            a_stem = (stemmer.stemWords(a))
            #print('стеммированная строка: ',a_stem)
            words_in_one_text = len(a_stem)
            for j in clean_st:
               b.append(a_stem.count(j)/words_in_one_text)
            Z.append(b)


        tst_in = Z
        L1 = sigmoid(n.dot(tst_in,W_1))
        L2 = sigmoid(n.dot(L1,W_2))
        #print(L2)

        L2 = L2[0]
        cap = 0.6

        if L2[0]>cap:
            tags.append('#политика')
        elif L2[1]>cap:
            tags.append('#спорт')
        elif L2[2]>cap:
            tags.append('#экономика')
    except Exception:
        tags.append('#none')


    return tags