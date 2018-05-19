learn_engine - программа машинного обучения в результате работы выдает файл synapses.json 
    НЕ запускать его , если не требуется переобучение сети (работает долго)

training_texts - тексты для обучения сети, хранятся в списке training_set в виде словарей:
 {'class': 'politics','text' :'''blablabla Putin and Trump f.. blalbla '''} вместо politics в зависимоти от темы есть economics и sports

tag_engine - собственно там лежит сама функция тэгирования tagger(), использует для подсчетов файл synapses.json 
 Пример использования: text_1 = 'СШа выразили обеспокоенность состоянием .....'
                       print(tagger(text_1))