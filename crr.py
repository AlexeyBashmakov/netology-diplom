"""
Построение CRR:
 - для всего срока и всех врачей
 - для всего срока и каждого врача
 - ежегодно для всех врачей
 - ежегодно для каждого врача
"""

"""
В base_analisys.py я метрику считал так:
                                                            количество уникальных пациентов бывших у этого врача больше одного раза
процент возвращающихся пациентов для конкретного врача = -----------------------------------------------------------------------------
                                                                           количество уникальных пациентов этого врача
в Интернет народ предлагает такую формулу для CRR:
      Ce - Cn
CRR = ------- * 100%
        Cb
где
Ce - количество пациентов на конец периода
Cn - количество новых пациентов, приобретенных за период
Cb - количество пациентов на начало периода
попробую посчитать вместе и сравнить, но по смыслу похоже одинаковое
"""

import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def correct_birthday(rec):
    """
    при построении распределения пациентов по возрасту обнаружились ошибочные данные в указанном возрасте в 39 приемах
    пришлось написать функцию для обработки 
    """
    yd1000 = lambda x: int(x.split("-")[0]) + 1000
    yd900 = lambda x: int(x.split("-")[0]) + 900
    yd800 = lambda x: int(x.split("-")[0]) + 800
    yd600 = lambda x: int(x.split("-")[0]) + 600
    yd100 = lambda x: int(x.split("-")[0]) + 100
    if rec.age > 1000:
        rec.birthday = f"{yd1000(rec.birthday)}{rec.birthday[4:]}"
        return rec.birthday
    elif rec.age > 900:
        rec.birthday = f"{yd900(rec.birthday)}{rec.birthday[4:]}"
        return rec.birthday
    elif rec.age > 800:
        rec.birthday = f"{yd800(rec.birthday)}{rec.birthday[4:]}"
        return rec.birthday
    elif rec.age > 600:
        rec.birthday = f"{yd600(rec.birthday)}{rec.birthday[4:]}"
        return rec.birthday
    elif rec.age > 100:
        rec.birthday = f"{yd100(rec.birthday)}{rec.birthday[4:]}"
        return rec.birthday
    else:
        return rec.birthday

def load_and_prepare() -> pd.DataFrame:
    """
    Функция загружает данные из csv в датафрейм и создает два новых столбца:
    с возрастом пациента типа int и датой приема типа datetime.date
    возвращает получившийся датафрейм
    """
    print("Загрузка данных подготовленных для базовой статистики")
    DF = pd.read_csv("to_base_statistics.csv")
    print(DF.info())
    # создаю новый столбец с возрастом пациента
    # функция из строкового представления возвращает кортеж: год, месяц, день
    # y = 0, то возвращает саму дату
    # y = 1, то день устанавливается в 1
    str_to_date = lambda x, y = 0: dt.date(int(x.split("-")[0]), int(x.split("-")[1]), int(float(x.split("-")[2])/(y*(float(x.split("-")[2])-1)+1))) if type(x) == str else dt.date.min
    DF["age"] = DF["birthday"].apply(lambda x: round((dt.date.today() - str_to_date(x, 0)).days / 365))
    # при построении распределения пациентов по возрасту обнаружились ошибочные данные в указанном возрасте в 39 приемах
    # пришлось написать функцию для обработки 
    DF["birthday"] = DF.apply(correct_birthday, axis = 1)
    # почему-то в функции следующие три строчки не отрабатывали
    yd800 = lambda x: int(x.split("-")[0]) + 800
    DF.loc[4832, "birthday"] = f"{yd800(DF.loc[4832, 'birthday'])}{DF.loc[4832, 'birthday'][4:]}"
    DF.loc[17566, "birthday"] = f"{yd800(DF.loc[17566, 'birthday'])}{DF.loc[17566, 'birthday'][4:]}"
    DF["age"] = DF["birthday"].apply(lambda x: round((dt.date.today() - str_to_date(x, 0)).days / 365))
    # создаю новый столбец, в котором дата имеет тип datetime.date для последующей работы с периодами
    DF["D"] = DF["date"].apply(str_to_date)
    #print(type(DF.loc[0, "date"]))
    #print(type(DF.loc[0, "birthday"]))
    #print(type(DF.loc[0, "age"]))
    #print(type(DF.loc[0, "D"]))
    #print(DF.age.max())
    # хочу оставить врачей проработавших дольше начала 2016 года, больше 100 дней и принявших больше 100 пациентов (да, такие есть)
#    doctors = DF[["client_cod", "ind_codeCat", "D"]]
    # начало работы каждого врача
    d_begin_work = DF[["ind_codeCat", "D"]].groupby("ind_codeCat").min().sort_values("D", ascending = True)
    # окончание работы каждого врача
    d_end_work = DF[["ind_codeCat", "D"]].groupby("ind_codeCat").max().sort_values("D", ascending = True)
    d_work = pd.merge(d_begin_work, d_end_work, on = "ind_codeCat")
    d_work.columns = ["begin", "end"]
    # продолжительность работы каждого врача
    d_work["period, days"] = d_work["end"] - d_work["begin"]
    # из типа datetime.timedelta перевожу в Int64
    d_work["period, days"] = d_work["period, days"].apply(lambda x: x.days)
    d_work.sort_values("period, days", ascending = False, inplace = True)
    # количество пациентов каждого врача
    d_patients = DF[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count()
    d_work = d_work.merge(d_patients, on = "ind_codeCat")
    d_work.columns = list(d_work.columns[:-1]) + ["patients"]
    # оставил врачей проработавших дольше начала 2016 года, больше 100 дней и принявших больше 100 пациентов (да, такие есть)
    d_work = d_work[(d_work["end"] > dt.date(2015, 12, 31)) & (d_work["period, days"] > 100) & (d_work["patients"] > 100)]
    
    
    DF = DF.merge(d_work.reset_index()["ind_codeCat"], on = "ind_codeCat").reset_index(drop = True)
    # C[set(C.columns) - set(["index", "value"])]

    # исключаю столбцы date и birthday, которые содержат строковые данные
    # и уже имеются столбцы с этими данными, но подходящего типа
    return DF[list(set(DF.columns) - set(["date", "birthday"]))]


DF = load_and_prepare()
print(DF.info())

