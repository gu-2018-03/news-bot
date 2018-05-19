import nltk
from nltk.corpus import stopwords
from pymorphy2 import MorphAnalyzer
from pymorphy2.tokenizers import simple_word_tokenize
from queue import Queue
import numpy as np
import numpy.linalg as la

punctuation = {',', ':', ';', '?', '!', '—', '«', '»'}

significant = {'NOUN', 'ADJF', 'VERB'}

stop = set(stopwords.words('russian'))
stop.add('который')



class Word(object):
    '''класс храянящий информацию о слове'''
    def __init__(self, normal_form, POS, original):
        self.base = normal_form
        self.POS = POS
        self.original = [original, ]
        self.weight = 1
        self.index = 0
        self.processed = False

    def inc(self, original):
        self.original.append(original)


class TextSource(object):
    '''  класс - тесктовой источник, хранит текст, разбивает на предложения выдает предложения по одноиу,
    разбивает преложения на слова, обрабатывает слова'''
    def __init__(self, text=None):
        self.words_dict = {}
        self.words_list = []
        self.text = text
        self.filename = ''

    def loadtext(self, filename):
        ''' загружает текст из файла'''
        with open(filename, 'r', encoding='utf-8') as f:
            self.text = f.read()
            self.filename = filename

    def sentence_generator(self):
        ''' генерирут предложения по одному '''
        begin = 0
        counter = 0
        length = len(self.text)
        while (begin < length):
            end = self.text.find('.', begin, length)
            if (end != -1):
                sentence = self.text[begin: end+1]
                begin = end+2
                counter +=1
                yield sentence
            else:
                raise StopIteration

    def tokenaize_sentence(self, sentence):
        '''разбивает предложение на слова'''
        # tokens = nltk.word_tokenize(sentence)
        tokens = simple_word_tokenize(sentence)
        return tokens

    def process_tokens(self, tokens):
        '''обработка слов, нормализация, опредление части речи, запись этих данных в структуру Word'''
        morphAnalizer = MorphAnalyzer()
        for token in tokens:
            if token not in punctuation:
                word_parced = morphAnalizer.parse(token)[0]
                word_normal = word_parced.normal_form
                if (word_normal not in stop) and (word_parced.tag.POS in {'NOUN', 'ADJF', 'VERB'}):
                    if word_normal in self.words_dict:
                        self.words_dict[word_normal].inc(token)
                    else:
                        self.words_dict[word_normal] = Word(word_normal, word_parced.tag.POS, token)
                    self.words_list.append(word_normal)

        for n, k in enumerate(self.words_dict.keys()):
            self.words_dict[k].index = n

    def process_text(self):
        '''обработка текста'''
        if self.text is not None:
            gen = self.sentence_generator()
            for sentence in gen:
                tokens = self.tokenaize_sentence(sentence)
                self.process_tokens(tokens)
            return True
        else:
            return False


class KeyWords2(TextSource):
    def __init__(self, text=None):
        TextSource.__init__(self, text)
        self.kw = []

    def build_model(self, dist):
        processed = self.process_text()

        if not processed:
            return
        n = len(self.words_dict.keys())
        self.A = np.zeros([n, n], dtype=np.float_)

        for n, word in enumerate(self.words_list):
            j = self.words_dict[word].index
            for adj_n in range(1, dist):
                if (n + adj_n) < len(self.words_list):
                    adj = self.words_list[n+adj_n]
                    if adj != '.':
                        i = self.words_dict[adj].index
                        self.A[i, j] = 1 #* (1 + (dist / 2 - (adj_n - 1)))
                        self.A[j, i] = 1 # * (1 + (dist / 2 - (adj_n - 1)))

        for col in range(self.A.shape[1]):
            self.A[:, col] = self.A[:, col] / self.A.shape[1]

    def recalc_pass(self, vect):
        return self.A @ vect

    def calculate_links(self):
        n = self.A.shape[1]
        vect = 100 * np.ones(n) / n

        lastVect = vect
        vect = self.recalc_pass(vect)
        i = 0
        while la.norm(lastVect - vect) > 0.01:
            lastVect = vect
            vect = self.recalc_pass(vect)
            i += 1
        vect = vect * 1000000
        self.kw  = list(self.words_dict.values())
        for i in range(vect.shape[0]):
            self.kw[i].weight = vect[i]

        self.kw = sorted(self.kw, key=lambda word: word.weight, reverse=True)
        return

    def get_keywords(self, n):
        n = n if n < len(self.kw) else len(self.kw)
        return [keyword.base for keyword in self.kw[:n]]


if __name__ == '__main__':

    kw_finder = KeyWords2()
    kw_finder.loadtext("news.txt")
    kw_finder.build_model(dist=5)
    kw_finder.calculate_links()
    keywords = kw_finder.get_keywords(10)
    print(keywords)




