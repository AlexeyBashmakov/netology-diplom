"""
предварительный анализ данных, наглядно описано их качество, аномалии, зависимости, приведены ссылки на код
признаки:
  данные пациентов:
   * код пациента (из строки перевожу в целый тип)
   * пол (строка, перевести в категории 0, 1)
   * возраст (из дня рождения получаю количество полных лет на момент приема, т.е. надо хранить день рождения; надо еще подумать)
   * страховая (строка, перевести в категории, определить количество и пронумеровать)
 данные приема:
   * дата приема
   * платный/бесплатный прием
   * диагноз, его код и название
   * код врача (специалиста)
"""
# cln_payments.dbf - оплата пациентами: код пациента (CLIENT_COD), код специалиста(IND_CODE), дата (DATE), сумма (PAYED)
# cln_diagnose.dbf - диагнозы пациентов: код пациента (CLIENT_COD), название диагноза (DIAG_NAME), код диагноза (DIAG_CODE), код специалиста(IND_CODE), дата (DATE)
# clndates.dbf - данные пациентов: код пациента (CLIENT_COD), день рождения (BIRTHDAY), пол (MG)
# cln_police.dbf - полисы: код страховой(INSURER_CO), код пациента (CLIENT_COD), номер полиса (NOM_POLICE)
# cln_priem.dbf - прием пациентов: код пациента (CLIENT_COD), дата (DATE), код специалиста (IND_CODE)
"""
из каких файлов что берем:
 - данные пациентов :
     код, день рождения -> возраст, пол - clndates.dbf
     страховая пациента (её код)  - cln_police.dbf
 - данные приема:
     дата приема, платный/бесплатный - cln_payments.dbf
     диагноз, код врача - cln_diagnose.dbf
при этом стоит еще использовать файл cln_priem.dbf для проверки качества данных
и, конечно, в разных файлах данные могут дублироваться и, как оказалось, отличаться
файл cln_priem.dbf пока решил не привлекать
"""

# ref_omsinsurer.dbf - страховые: код (INDEX), название (FULLNAME)
# docs.dbf - какие-то документы: дата, сумма, код пациента
# kvitancia.dbf - квитанции: код пациента, ФИО, дата, сумма, текст квитанции
# cln_actions.dbf - 13 действия с пациентами: код пациента, код действия, сумма
# cln_health.dbf - 18 что-то про пациентов: код пациента, дата, поле DIAGNOSE ссылается на поле INDEX файла cln_diagnose.dbf
# diagnose.dbf - диагнозы(?)
# personal.dbf - персонал: код специалиста (IND_CODE), ФИО (FIRST_LAST)

import dbf
import datetime as dt
import pandas as pd
#import numpy as np
from numpy import nan, isnan

"""
проверка данных пациентов
"""
def coding_insurers(arg):
    """
    Функция коду страховой ставит в соответствие целое число:
    _3R60ODN96 - 0
    ........CA - 1
    ........8X - 2
    ........FR - 3
    ........9Z - 4
    """
    #if isnan(arg):
    if arg is nan:
        return nan
    else:
        if arg[-2:] == "96":
            return 0
        elif arg[-2:] == "CA":
            return 1
        elif arg[-2:] == "8X":
            return 2
        elif arg[-2:] == "FR":
            return 3
        elif arg[-2:] == "9Z":
            return 4
        else:
            return nan

def client_datas_to_csv():
    """
    Функция загружает данные пациентов из файлов dbf 
    и сохраняет нужную информацию в формате csv,
    для последующей работы методами pandas
    """
    # загружаем файл с кодом пациента, его днём рождения и полом
    f = "clndates.dbf"
    table = dbf.Table("Dbc\\" + f)
    table.open()
    print("Файл:", f)
    print("Длина таблицы:", len(table))
    #print(table[-1])
    # для записи данных в csv будем использовать функционал pandas
    # а для создания датафрейма сначала создаем словарь с данными из одной строки таблицы dbf
    rec = {"client_cod": int(table[0]["CLIENT_COD"]), "birthday": table[0]["BIRTHDAY"], "gender": table[0]["MG"]}
    df = pd.DataFrame()
    # цикл проходит по всем строкам таблицы dbf
    # используем доступ по индексу для обработки возможных исключительных ситуаций
    for i in range(1, len(table)):
        try:
            # в файлах dbf этой базы код клиента представлен строкой состоящей из чисел
            # на случай сбоев ПО я проверяю строку на то, что все её символы числовые
            if table[i]["CLIENT_COD"].strip().isnumeric():
                # предварительный просмотр данных файла показал, что в нем присутствует фиктивный пациент с кодом 1
                # и таких записей может быть несколько
                # коды реальных пациентов многозначны
                # пропускаю также строки где не указан пол пациента (стоит пробел)
                if (int(table[i]["CLIENT_COD"]) > 1) and (table[i]["MG"] != " ") and (table[i]["BIRTHDAY"] is not None):
                    rec = {"client_cod": int(table[i]["CLIENT_COD"]), "birthday": table[i]["BIRTHDAY"], "gender": table[i]["MG"]}
                else:
                    # пропускаю строку с фиктивным пациентом
                    continue
            else:
                # если в строке не только числовые символы, то пропускаю эту строку
                print("Record", i, "is not numeric:", table[i]["CLIENT_COD"], ", date:", table[i]["BIRTHDAY"])
                continue
        except Exception as e:
            # перехватываю такое общее исключение, лень было обрабатывать по отдельности
            # оправдываю себя тем, что данное приложение не производственное
            print("Error:\n", e, sep = "")
            print("Record:", i)
        else:
            # если исключение не произошло, то добавляю в датафрейм прочитанную из строки таблицы dbf
            df = pd.concat([df, pd.DataFrame(rec, index = [0])], ignore_index = True)
            if i % 1000 == 0:
                print(i)

    # создаем столбец, в котором пол пациента переведен в целый тип: М = 1, Ж = 0
    df.loc[:, "genderCat"] = df["gender"].apply(lambda x: 1 if x == "М" else 0)
    print(df.info())
    table.close()
    
    # загружаем файл с данными полисов
    f = "cln_police.dbf"
    table = dbf.Table("Dbc\\" + f)
    table.open()
    print("Файл:", f)
    print("Длина таблицы:", len(table))
    #print(table[-1]["CLIENT_COD"])
    # для каждой записи в таблице
    for record in table:
        # добавляю в созданный ранее датафрейм столбец с кодом страховой каждого пациента
        # но пропускаю пустые строки, чтобы были пустые (nan) значения
        if record["INSURER_CO"][0:4] == "_3R6":
            df.loc[df["client_cod"] == int(record["CLIENT_COD"]), "insurer"] = record["INSURER_CO"]
        # пустых строк ("          ") было всего две, поэтому их пропуск не повлияет на результаты обработки
    
    # создаем столбец, в котором код страховой пациента заменен на целое число
    #df.loc[:, "insurerCat"] = df["insurer"].apply(coding_insurers)
    # почему-то здесь python не захотел создавать так новый столбец до сохранения датафрейма в csv
    # как создал после сохранения и повторной загрузки (см. тождественную строчку ниже)
    
    # сохраняю датафрейм в csv
    df.to_csv("clndates.csv", index = False, date_format = "%Y-%m-%d")
    table.close()
    
    df1 = pd.read_csv("clndates.csv")
    df1.loc[:, "insurerCat"] = df1["insurer"].apply(coding_insurers)
    df1.to_csv("clndates.csv", index = False, date_format = "%Y-%m-%d")

def priems_to_csv():
    """
    Функция загружает данные приемов из файлов dbf 
    и сохраняет нужную информацию в формате csv,
    для последующей работы методами pandas
    """
    # загружаем файл с оплатой пациентами: код пациента (CLIENT_COD), код специалиста(IND_CODE), дата (DATE), сумма (PAYED)
    f = "cln_payments.dbf"
    # каждая строка представляет запись об операции произведенной с пациентом
    # поэтому в день м.б. несколько записей с одним или несколькими платежами (нулевыми или нет)
    # следовательно, если для пациента на данный день присутствует ненулевой платеж, то считаем прием платным (уточнить!!!)
    # если только нулевые платежи, то прием бесплатный
    table = dbf.Table("Dbc\\" + f)
    table.open()
    print("Файл:", f)
    print("Длина таблицы:", len(table))
    #print(table[-1])
    # для записи данных в csv используем функционал pandas
    df = pd.DataFrame()
    df1 = pd.DataFrame()
    # в файле присутствуют записи для одного врача, но с двумя кодами
    # следующая функция старый код этого врача меняет на новый
    chernovaAS = lambda x: "_5FY0WLR92" if x == "52553085  " else x
    # цикл проходит по всем строкам таблицы dbf
    # используем доступ по индексу для обработки возможных исключительных ситуаций
    for i in range(1, len(table)):
        try:
            # в файлах dbf этой базы код клиента представлен строкой состоящей из чисел
            # на случай сбоев ПО я проверяю строку на то, что все её символы числовые
            if table[i]["CLIENT_COD"].strip().isnumeric():
                # предварительный просмотр данных файла показал, что в нем присутствует фиктивный пациент с кодом 1
                # и таких записей может быть несколько
                # коды реальных пациентов многозначны
                # также присутствуют записи с кодами специалистов:
                # "74711617  " - это администратор системы
                # "45805327  " - РЕГИСТРАТОР
                # "_4EC17JRCX" - яБит-Сервис
                # это очевидно (или не очевидно? - уточнить) не врачи, эти записи тоже пропускаю
                if (table[i]["IND_CODE"] not in ["74711617  ", "45805327  ", "_4EC17JRCX"]) and (int(table[i]["CLIENT_COD"]) > 1):
                    rec = {"client_cod": int(table[i]["CLIENT_COD"]), \
                           "ind_code": chernovaAS(table[i]["IND_CODE"]), \
                           "date": table[i]["DATE"], \
                           "pay": float(table[i]["PAYED"])}
                else:
                    # пропускаю строку с фиктивным пациентом и не врачами (см. список в if)
                    continue
            else:
                # если в коде пациента не только числовые символы, то пропускаю эту строку
                print("Record", i, "is not numeric:", table[i]["CLIENT_COD"], ", date:", table[i]["DATE"])
                rec = {"client_cod": table[i]["CLIENT_COD"], \
                       "ind_code": table[i]["IND_CODE"], \
                       "date": table[i]["DATE"], \
                       "pay": float(table[i]["PAYED"])}
                df1 = pd.concat([df1, pd.DataFrame(rec, index = [0])], ignore_index = True)
                # здесь оказываются коды пациентов или _BUSY12345 (и тогда есть код врача)
                # или код страховой (и кода врача нет)
                # думаю не использовать эту информацию
                continue
        except Exception as e:
            # перехватываю такое общее исключение, лень было обрабатывать по отдельности
            # оправдываю себя тем, что данное приложение не производственное
            print("Error:\n", e, sep = "")
            print("Record:", i)
            #break
        else:
            # если исключение не произошло, то добавляю в датафрейм прочитанную из строки таблицы dbf
            df = pd.concat([df, pd.DataFrame(rec, index = [0])], ignore_index = True)
            if i % 1000 == 0:
                print(i)
                #break

    table.close()
    print(df.info())
    #print(df1.info())
    #df.to_csv("cln_payments.csv", index = False, date_format = "%Y-%m-%d")
    # отбрасываем повторяющиеся строки
    print("отбрасываем повторяющиеся строки")
    df.drop_duplicates(inplace = True, ignore_index = True)
    print(df.info())
    # группируем строки по коду пациента, коду врача, дате приема
    # суммируем значения в оставшемся столбце - платеж (pay)
    # получаем датафрейм с мультииндексом, в котором
    # сбрасываем мультииндекс так, что каждая строка мультииндекса разворачивается в отдельную строку с единичным индексом
    print("работы с группировкой, суммированием и сбросом индексов")
    df_ = df.groupby(["client_cod", "ind_code", "date"]).sum().reset_index()
    del df
    # создаем новый датафрейм, чтобы данные старого не влияли
    # получили датафрейм в котором каждая строка соответствует отдному приему пациента
    print(df_.info())
    # создаем столбец, в котором тип приема указывается целым числом: платный = 1, бесплатный = 0
    # т.е. если сумма в столбце платеж (pay) отличен от 0, то прием платный
    print("создаем столбец с типом приема")
    df_.loc[:, "payCat"] = df_["pay"].apply(lambda x: 1 if x else 0)
    print(df_.info())
    # для сохранения данных без диагнозов
    df_.to_csv("cln_payments_cleared.csv", index = False, date_format = "%Y-%m-%d")
    
    # загружаем файл с диагнозами пациентов: код пациента (CLIENT_COD), название диагноза (DIAG_NAME), код диагноза (DIAG_CODE), код специалиста(IND_CODE), дата (DATE)
    f = "cln_diagnose.dbf" # название диагноза (DIAG_NAME) использовать не будем
    table = dbf.Table("Dbc\\" + f)
    table.open()
    print("Файл:", f)
    print("Длина таблицы:", len(table))
    #print(table[-1])
    diagnoseDF = pd.DataFrame()
    for i in range(1, len(table)):
        try:
            if table[i]["CLIENT_COD"].strip().isnumeric():
                if int(table[i]["CLIENT_COD"]) > 1:
                    rec = {"client_cod": int(table[i]["CLIENT_COD"]), "date": table[i]["DATE"], "diag_code": table[i]["DIAG_CODE"]}
                else:
                    continue
            else:
                print("Record", i, "is not numeric:", table[i]["CLIENT_COD"], ", date:", table[i]["DATE"])
                continue
        except Exception as e:
            print("Error:\n", e, sep = "")
            print("Record:", i)
            #break
        else:
            diagnoseDF = pd.concat([diagnoseDF, pd.DataFrame(rec, index = [0])], ignore_index = True)
            if i % 1000 == 0:
                print(i)
    table.close()
    print("датафрейм диагнозов")
    print(diagnoseDF.info())
    
    # для добавления кода диагноза (DIAG_CODE) к приему
    # буду к датафрейму df_ добавлять из датафрейма diagnoseDF столбец diag_code
    # с помощью pandas.merge(left, right, how="inner", on=None, left_on=None, right_on=None)
    # result = pd.merge(time_live, users, how = "inner", left_on = "userId", right_on = "userId")
    print("объединяем датафреймы приемов и диагнозов")
    df = pd.merge(df_, diagnoseDF, how = "inner", left_on = ["client_cod", "date"], right_on = ["client_cod", "date"])
    print(df.info())
    # после внешнего (how = "outer") соединения датафреймов оказалось, что в cln_diagnose.dbf присутствуют записи с CLIENT_COD и DATE
    # которых нет в cln_payments.dbf
    # получается, что есть пациент, дата и диагноз, но нет врача. пациент для ОМС?
    # если я анализирую статистику пациентов по врачам (в том числе), то диагнозы без врачей бессмысленны
    # поэтому надо соединять данные из cln_payments.dbf с данными из cln_diagnose.dbf с помощью внутреннего соединения
    # отбрасываем повторяющиеся строки
    print("отбрасываем повторяющиеся строки")
    df.drop_duplicates(inplace = True, ignore_index = True)
    print(df.info())
    
    df.to_csv("cln_payments_diagnoses.csv", index = False, date_format = "%Y-%m-%d")
    # однако в csv попадаются строки с будущей датой (дата базы 22.06.22)
    # это потому что пациента полечили давно, а денег не получили, поэтому записали на свободное время в будущем

    # не использую эту информацию
    #df1.to_csv("cln_payments1.csv", index = False, date_format = "%Y-%m-%d")

def diagnose_to_csv():
    """
    Функция загружает данные диагнозов пациентов на приемах из dbf
    и сохраняет в csv.
    Сделана для временного использования для анализа файла dbf
    """
    # загружаем файл с диагнозами пациентов: код пациента (CLIENT_COD), название диагноза (DIAG_NAME), код диагноза (DIAG_CODE), код специалиста(IND_CODE), дата (DATE)
    f = "cln_diagnose.dbf" # название диагноза использовать не будем
    table = dbf.Table("Dbc\\" + f)
    table.open()
    print("Файл:", f)
    print("Длина таблицы:", len(table))
    #print(table[-1])
    diagnoseDF = pd.DataFrame()
    for i in range(1, len(table)):
        try:
            if table[i]["CLIENT_COD"].strip().isnumeric():
                if int(table[i]["CLIENT_COD"]) > 1:
                    rec = {"client_cod": int(table[i]["CLIENT_COD"]), "date": table[i]["DATE"], "diag_code": table[i]["DIAG_CODE"]}
                else:
                    continue
            else:
                print("Record", i, "is not numeric:", table[i]["CLIENT_COD"], ", date:", table[i]["DATE"])
                continue
        except Exception as e:
            print("Error:\n", e, sep = "")
            print("Record:", i)
            #break
        else:
            diagnoseDF = pd.concat([diagnoseDF, pd.DataFrame(rec, index = [0])], ignore_index = True)
            if i % 1000 == 0:
                print(i)
    table.close()
    print("датафрейм диагнозов")
    print(diagnoseDF.info())
    
    diagnoseDF.to_csv("diagnose.csv", index = False, date_format = "%Y-%m-%d")

def union_datas():
    """
    Функция объединяет данные clndates.csv и cln_payments_diagnoses.csv
    через внутреннее соединение датафреймов куда загружаются эти данные
    а также создаем столбцы с в которых код врача, код диагноза переведены в целочисленные значения
    """
    df = pd.read_csv("clndates.csv")
    df0 = pd.read_csv("cln_payments_diagnoses.csv")
    # объединяю данные clndates.csv и cln_payments_diagnoses.csv
    DF = pd.merge(df0, df, how = "inner", left_on = "client_cod", right_on = "client_cod")
    # для создания столбца в котором код врача заменен целым числом
    # сначала создадим словарь сопоставляющий каждому уникальному коду врача целое число
    ind_code = dict()
    # в цикле его заполним
    for i, code in enumerate(DF.ind_code.unique()):
        # в словаре уникальный код врача это ключ для целого числа
        ind_code[code] = i
    # создаем столбец с помощью лямбда функции, которая просто возвращает целое число из словаря по коду врача
    DF.loc[:, "ind_codeCat"] = DF["ind_code"].apply(lambda c: ind_code[c])
    # тоже делаем для замены кода диагноза целым числом
    diag_code = dict()
    for i, code in enumerate(DF.diag_code.unique()):
        diag_code[code] = i
    DF.loc[:, "diag_codeCat"] = DF["diag_code"].apply(lambda c: diag_code[c])
    # из датафрейма убирем столбцы 
    # ind_code, pay, diag_code, gender, insurer
    # которые содержат данные уже переведенные в целочисленные категории
    # но данные с этими столбцами сохраню
    DF.to_csv("cln_payments_diagnoses_datas_full.csv", index = False, date_format = "%Y-%m-%d")
    DF = DF[["client_cod", "date", "payCat", "birthday", "genderCat", "insurerCat", "ind_codeCat", "diag_codeCat"]]

    # сохраняю данные для обработки
    DF.to_csv("to_base_statistics.csv", index = False, date_format = "%Y-%m-%d")


T0 = dt.datetime.now()
#client_datas_to_csv()
#priems_to_csv()
#diagnose_to_csv()
T1 = dt.datetime.now()
print(T1 - T0)
# при внешнем соединении время работы было 4 мин 21 сек, процессор работал на максимальной частоте
# при внутреннем почему-то больше 13 мин, но процессор работал на частоте меньше 1ГГц
union_datas()
if True:
    print("Загрузка данных пациентов из csv в датафрейм...")
    df = pd.read_csv("clndates.csv")
    print(df.info())
    print("Кодов страховых:", len(df.insurerCat.unique()))
    print("Кодов пациентов:", len(df.client_cod.unique()))

    print("\nЗагрузка данных приемов из csv в датафрейм...")
    # проверка на реальных врачей
    df0 = pd.read_csv("cln_payments_diagnoses.csv")
    df1 = pd.read_csv("personal.csv")
    #for code in df0.ind_code.unique():
    #    print(code, ":", df1[df1["ind_code"] == code].iloc[0]["family"])
    print(df0.info())
    print("Всего врачей:", len(df0.ind_code.unique()))
    print("Кодов пациентов:", len(df0.client_cod.unique()))
    print("Кодов диагнозов:", len(df0.diag_code.unique()))
    
    print("Загрузка данных подготовленных для базовой статистики")
    DF = pd.read_csv("to_base_statistics.csv")
    print(DF.info())
    #print("Всего врачей:", len(DF.ind_code.unique()))
    #print(DF.ind_code.unique())
#    diag_code = dict()
#    for i, code in enumerate(DF.diag_code.unique()):
        #print(f"i: {i:2}, code: {code}")
#        diag_code[code] = i
    #print(ind_code)
#    DF.loc[:, "diag_codeCat"] = DF["diag_code"].apply(lambda c: diag_code[c])
#    print(DF.info())



