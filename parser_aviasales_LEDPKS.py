from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.chrome.options import Options
import pandas as pd
from datetime import datetime,timedelta,date
import schedule

#Функция для отбора цены
def find_num(list_text):
    out = []
    for text in list_text:
        out.append(int(''.join(c if c.isdigit() else '' for c in text)))
    return out

def parsing_of_data():
    '''основная функция парсера, находящая все
    необходимые теги и добавляющая их в файл csv '''
    try:
            #формируем ссылку на поиск билетов на неделю после нынешней даты 
        current_date = str(date.today()+timedelta(days=7))
        current_date = current_date[-2:]+current_date[5:7]
        url = 'https://www.aviasales.ru/search/LED'+current_date+'PKC1'
        #Открываем основной файл
        try:
            basik_data = pd.read_csv('parser_data.csv', 
                                    index_col='Unnamed: 0')
        #если нет создася новый
        except:
            pass

        options = Options()
        options.add_argument("window-size=1920,1080")
        
        # Бывает, что подобранный файл ассоциируется с неправильным форматом, 
        # для этого был подготовлен подоходящий драйвер
        try:
            service = Service(executable_path=ChromeDriverManager().install())
        except:    
            service = Service(executable_path='ChromDriver/usr/local/bin/chromedriver')
            
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        html = driver.page_source
        parse = BeautifulSoup(html, features="html.parser")

        #Список в котором будет сохранятся информация
        data = []

        #цена
        price = parse.find_all('div', class_='s__mvNEtCM6SuXfR8Kopm7T s__pPCa7rJcciF16fYn5k_2 s__wfLcPf6IF1Ayy7uJmdtH')
        #особенность билета (самый дешевый итд)
        the_most = (parse
                    .find_all('span', class_='s__WJBFOjXpaWb4CntP5Bga s__N1ADMCTrJPLlY8XRaASO s__OXITWCfPGlAr5oHMRYBX s__Ip7JWzhA_RGEx3FrzanV')
                )
        #Время полета
        time_in_flight = parse.find_all('span','s__iPfYoBmp1qVHqkPI5MCQ s__Lrz8pict9CWP2T8btbYb s__PAD5qI5zjZJVo59x3Acm')
        #Время взлета
        time_take_off = parse.find_all('div','s__gG4lAHv1aE4OfRaT5O32 s__IlVcqCLz3_J3IURWpWIw s__S95F4b9LpJpuwp1QdgiP')
        #Время приземления 
        time_landing = parse.find_all('div','s__gG4lAHv1aE4OfRaT5O32 s__IlVcqCLz3_J3IURWpWIw s__mu9qt4cBA0gRWiJccVf2')

        #Дата вылетов и прилетов с городами, сразу обрежим города 
        flight_dates = (parse
                        .find_all('span', 's__iPfYoBmp1qVHqkPI5MCQ s__Lrz8pict9CWP2T8btbYb s__JQPma7iRwaXhu6sgs2Nv s__st8iGUwwQEz6lc9CRwIO')
                        [1::2])
        # В цикле отберем нечетные даты как даты вылета, четные как даты прилета
        departure_date = []
        departure_weekday = []
        arrival_date = []
        arrival_weekday = []
        
        for i in range(len(flight_dates)):
            if i%2==0:
                departure_date.append(flight_dates[i])
                departure_weekday.append(flight_dates[i])
            else:
                arrival_date.append(flight_dates[i])
                arrival_weekday.append(flight_dates[i])
                
                
        # Достаем компании предоставляющие услуги по билетам
        #Пустой список хранящий компании       
        air_companes =[]
        #Идем в цикле в куску кода хранящим названия компаний
        for i in parse.find_all('div','s__iLii9nj713he1PD8WMQ9'):
            #Добавляем списоки в air_companes хранящих все компании для каждого из билета
            air_companes.append([j.img['alt'] for j in 
                    i.find_all('div','s__OxH0KVgAJVg2DNGFFx0s s__FbGKNa50kfTXi9g6iPe5 s__VKzft3dOalScmeO2eH3e s__IfNnlCoxL4fHuW2lW3Xl')]
                    )
        #Добавляем полученные данные в общий массив
        #цена
        data.append(find_num([i.text for i in price ]))
        #Особенность, так как она присудствует не везде, добавим общее значение для пропусков
        data.append([i.text for i in the_most])
        #Цикл заполняет недостоящие значения
        for i_n in range(len(price)-len(the_most)):
            data[1].append('отсутствует')
        #Время полета
        data.append([i.text.replace('\u200a', '')[8:] for i in time_in_flight])

        #Время взлета
        data.append([i.text for i in time_take_off])

        #Время посадки
        data.append([i.text for i in time_landing])

        #дата вылета
        data.append([i.text.replace('\xa0', '')[:-3] for i in departure_date])

        #день недели вылета 
        data.append([i.text.replace('\xa0', '')[-2:] for i in departure_weekday])

        #дата прибытия
        data.append([i.text.replace('\xa0', '')[:-3] for i in arrival_date])

        #день недели прибытия
        data.append([i.text.replace('\xa0', '')[-2:] for i in arrival_weekday])
        
        #компании
        data.append(air_companes)


        #Названия колонок датафрейма
        name_cols = ['цена',
                    'особенность',
                    'время в полете',
                    'время вылета',
                    'время посадки',
                    'дата вылета',
                    'день недели вылета',
                    'дата посадки',
                    'день недели посадки',
                    'авиакомпании'
                    ]
        #Иногда прасинг ссрывается и выдает пустой датафрейм 
        if data[0] == []:
            print('Неудачный парсинг ', datetime.now())
            parsing_of_data()
        else:
            #формируем датафрейм
            parser_data = pd.DataFrame.from_dict(dict(zip(name_cols,data)))
            parser_data['время парсинга'] = datetime.now()
            
            #Проверка наличия исходных данных 
            try:
                parser_data = pd.concat([basik_data, parser_data],
                                    ignore_index=True)
            except NameError: 
                pass
            # Добавляем или созданем спарсенные данные 
            parser_data.to_csv('parser_data.csv', 
                            index=True)
            print('Парсинг удался ', datetime.now())
    except:
            print('Не получилось ', datetime.now())   
   
def start_process():
    schedule.every(1).hour.do(parsing_of_data) 
    print('Процесс пошел')
    while True:
        schedule.run_pending()
        time.sleep(1)
        
if __name__ == '__main__':
    start_process()