import snowballstemmer as sn
from training_texts import training_set
import numpy as n
import json
import time
start_time = time.time()

'''
1-я часть. 
Работа по векторизации слов в тексте
'''

#texts = [text_1p,text_2p,text_3p,text_4p,text_5s,text_6s,text_7s,text_8s, text_9e,text_10e,text_11e,text_12e,test_13p,test_14p,test_15p,test_16p,test_17s,test_18e,test_19e,test_20e] #!!!пока вручную править
#join_texts =text_1p+text_2p+text_3p+text_4p+text_5s+text_6s+text_7s+text_8s+text_9e+text_10e+text_11e+text_12e+test_13p+test_14p+test_15p+test_16p+test_17s+ test_18e+ test_19e+ test_20e#!!!
texts =[]
join_texts = ''
for i in training_set:
    text = i.get('text')
    texts.append(text)
    join_texts = join_texts + text

split_words_texts = join_texts.split()
#удалаяем ненужные слова


#выделяем корни слов(стемминг)
stemmer = sn.RussianStemmer()

#получаем очищенный и стеммированный текст
S = ' '.join(stemmer.stemWords(split_words_texts))
S = S.lower()

#строим словарь всех нормализ слов всех текстов (просто присваиваем номера словам)
V = {}
m=1
for w in S.split():
    V.update({w:m})
    m+=1

#удаляем повторяющиеся слова
st =S.split()
clean_st = []
for i in st:
    if i not in clean_st:
        clean_st.append(i)
# и ненужные
stop_list = 'но и с от по над в об у'.split()
for word in clean_st:
    if word in stop_list:
        clean_st.remove(word)
#print('чистый список: ',clean_st)

#строим массив вхождений
X = []
for i in texts:
    #print('текст: ',i)
    b=[1]# *тут первые единицы для машинного обучения нужны
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
    X.append(b)

print(X)


'''
2-я часть. 
Работа с forward propagation
'''

#забиваем вектор весов (рандомный, в среднем примерно ноль)
W_1 = 2*n.random.random((len(X[0]), 4)) -1 #4или3?
#print('матрица: ', W_1 )
W_2 = 2*n.random.random((4, 3)) -1
#print('матрица: ', W_2 )

#словарь векторизации тем
classifcation_dict = {
    'politics': [1,0,0],
    'sports': [0,1,0],
    'economics': [0,0,1]
    }



#Y= [[1,0,0],[1,0,0],[1,0,0],[1,0,0],[0,1,0],[0,1,0],[0,1,0],[0,1,0],[0.3,0,1],[0.4,0,1],[0.2,0,1],[0,0,1],[1,0,0],[1,0,0],[1,0,0],[1,0,0],[0,1,0],[0,0,1],[0,0,1],[0,0,1]] #!!!!!! пока вручную править
Y=[]
for i in training_set:
    v = i.get('class')
    vector = classifcation_dict.get(v)
    Y.append(vector)


#вводим сигмоиду
def sigmoid(x):
    return 1/(1+n.exp(-1*x))
#и ее дифференциал
def div_sigmoid(x):
    return x*(1-x)

#проверка работоспособности слоев

def forward_propagation(x,w1,w2):
    l1 = sigmoid(n.dot(x,w1))
    l2 = sigmoid(n.dot(l1,w2))
    return l1,l2

'''
3-я часть.
Работа с back propagation
'''
#проверка ошибки

def back_propagation(x, y,L1,L2, weight_1, weight_2, alpha):

    l1= n.array
    l1= L1
    x1 = n.array
    x1 = x
    l1_t = n.transpose(l1)
    x_t = n.transpose(x1)
    w2_t = n.transpose(weight_2)

    l2_error = y - L2
    l2_delta = l2_error* div_sigmoid(L2)

    l1_error = n.dot(l2_delta, w2_t)
    l1_delta = l1_error*div_sigmoid(L1)

    div_J2 = n.dot(l1_t,l2_delta)
    div_J1 = n.dot(x_t, l1_delta)

    weight_2 = weight_2 + alpha*div_J2
    weight_1 = weight_1 + alpha*div_J1

    return weight_1, weight_2, l2_error

'''
этап обучения
'''

i=0
while i <10000:
    layer_1,layer_2 = forward_propagation(X,W_1,W_2)
    W_1, W_2, d_err = back_propagation(X,Y,layer_1,layer_2,W_1,W_2, 0.5)
    i+=1
    if i%1000 == 0:
        print('i1=',d_err)


print('W_1 =',W_1)
print('W_2 =',W_2)



#запись в фйал 2 веса и список всех слов
synapse = {'W_1': W_1.tolist(), 'W_2': W_2.tolist(), 'clean_st': clean_st}
synapse_file = "synapses.json"
with open(synapse_file, 'w') as outfile:
        json.dump(synapse, outfile, indent=4, sort_keys=True)






print("--- %s seconds ---" % (time.time() - start_time))