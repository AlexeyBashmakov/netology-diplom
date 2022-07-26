"""
Построение CRR:
 + для всего срока и всех врачей
 + для всего срока и каждого врача
 + ежегодно для всех врачей
 + ежегодно для каждого врача
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
по смыслу обе формулы одинаковые
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
    #print(DF.info())
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
    # в столбце age (выше) я получил возраст пациента на момент исследования (сейчас)
    # здесь я получаю возраст пациента на момент приема
    DF["A"] = DF.apply(lambda x: round((str_to_date(x.date, 0) - str_to_date(x.birthday, 0)).days / 365), axis = 1)
    # создаю новый столбец, в котором дата имеет тип datetime.date для последующей работы с периодами
    DF["D"] = DF["date"].apply(str_to_date)
    # хочу оставить врачей проработавших дольше начала 2016 года, больше 100 дней и принявших больше 100 пациентов (да, такие есть)
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
    # после такого соединения коды врачей идут не последовательно

    # коды врачей заменю другим целым числом, потому что сейчас коды не идут последовательно
    # сначала создадим словарь сопоставляющий каждому уникальному коду врача целое число
    ind_code = dict()
    # в цикле его заполним
    for i, code in enumerate(DF.ind_codeCat.unique()):
        # в словаре уникальный код врача это ключ для целого числа
        ind_code[code] = i
    # создаем столбец с помощью лямбда функции, которая просто возвращает целое число из словаря по коду врача
    DF.loc[:, "ind_codeCat"] = DF["ind_codeCat"].apply(lambda c: ind_code[c])


    # исключаю столбцы date и birthday, которые содержат строковые данные
    # и уже имеются столбцы с этими данными, но подходящего типа
    return DF[list(set(DF.columns) - set(["date", "birthday", "age"]))]

def color_string(n: int) -> str:
  """
  Функция по индексу строит строку цвета
  """
  r, g, b = 0, 0, 0
  if n // 2 == 0:
    r = 125 * (n % 2 + 1)
  elif n // 2 == 1:
    g = 125 * (n % 2 + 1)
  else:
    b = 125 * (n % 2 + 1)
  return f"#{r:02x}{g:02x}{b:02x}"

if __name__ == "__main__":
    DF = load_and_prepare()

    """
    CRR для всего срока и всех врачей
    """
    # берем столбец client_cod, группируем и считаем количество строк
    # по сути получаем количество посещений конкретным пациентом за все время
    # DF["client_cod"] - получается Series, value_counts для Series не получает subset (как для датафрейма) и normalize по умолчанию False
    df = DF["client_cod"].value_counts().reset_index()
    df.columns = list(df.columns[:-1]) + ["priems"]

    print("CRR для всего срока и всех врачей:\n", round(df[df.priems > 1]["index"].count() / df["index"].count(), 3))

    """
    CRR для всего срока и каждого врача
    """
    # берем столбцы client_cod и ind_codeCat, группируем сначала по первому, потом по второму и считаем количество строк
    # по сути получаем количество посещений конкретным пациентом конкретного врача
    df = DF[["client_cod", "ind_codeCat"]].value_counts(["client_cod", "ind_codeCat"]).reset_index()
    df.columns = list(df.columns[:-1]) + ["priems"]

    # df[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count() - количество уникальных пациентов врача
    # df[df.priems > 1][["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count() - количество пациентов бывших у врача больше одного раза
    df = pd.merge(df[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count(), \
                  df[df.priems > 1][["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count(), \
                  on = "ind_codeCat").reset_index()
    df.columns = ["ind_codeCat", "all_unique", "repeat"]
    df["percent"] = (df["repeat"]/df["all_unique"]).apply(round, args = (3,))

    print("CRR для всего срока и каждого врача:\n", df)

    """
    CRR ежегодно для всех врачей
    """
    CRR_by_year = list()
    for i in range(2014, 2022):
        # выбираем строки датафрейма, которые соответствуют i-му году
        df = DF[(DF.D > dt.date(i-1, 12, 31)) & (DF.D < dt.date(i+1, 1, 1))]["client_cod"].value_counts().reset_index()
        df.columns = list(df.columns[:-1]) + ["priems"]
        CRR_by_year.append(round(df[df.priems > 1]["index"].count() / df["index"].count(), 3))
        print(f"CRR за {i} год для всех врачей:", CRR_by_year[-1])

    """
    CRR ежегодно для каждого врача
    """
    # датафрейм, в который будут записываться CRR для каждого врача за каждый год
    CRR_by_all = pd.DataFrame(data = {"ind_codeCat": DF["ind_codeCat"].unique()})
    for i in range(2014, 2022):
        # выбираем строки датафрейма, которые соответствуют i-му году
        df = DF[(DF.D > dt.date(i-1, 12, 31)) & (DF.D < dt.date(i+1, 1, 1))][["client_cod", "ind_codeCat"]].value_counts(["client_cod", "ind_codeCat"]).reset_index()
        df.columns = list(df.columns[:-1]) + ["priems"]
        df = pd.merge(df[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count(), \
                      df[df.priems > 1][["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count(), \
                      on = "ind_codeCat").reset_index()
        df.columns = ["ind_codeCat", "all_unique", "repeat"]
        # вычисляю процент и округляю до 3-х цифр после запятой
        df["percent"] = (df["repeat"]/df["all_unique"]).apply(round, args = (3,))
        # добавляю в датафрейм столбец с вычисленным процентом, но через внешнее соединение, чтобы не потерять данные
        CRR_by_all = CRR_by_all.merge(df[["ind_codeCat", "percent"]], how = "outer", on = "ind_codeCat")
        # столбцы датафрейма именуются годами
        CRR_by_all.columns = list(CRR_by_all.columns[:-1]) + [str(i)]
    # пропущенные значения заполняю нулями
    CRR_by_all.fillna(0, inplace = True)
    # транспонирую для облегчения построения визуализаций
    CRR_by_all_transp = CRR_by_all.T
    #print(CRR_by_all_transp)
    print(CRR_by_all)

    if True:
        fig, ax = plt.subplots()
        # список для легенды
        leg = []
        # оставил: 0, 2, 3, 4, 7, 8 - коды врачей
        cols = [0, 2, 3, 4, 7, 8]
        for i, col in enumerate(cols): #CRR_by_all_transp.columns: - решил все не строить, т.к. у некоторых или мало значений, или не работают уже
            ax.plot(CRR_by_all_transp.index.values[1:], CRR_by_all_transp[col].iloc[1:], c = color_string(i), alpha = 0.5)
            leg.append(col)
        ax.grid(True)
        ax.set_xlabel("Год")
        ax.set_ylabel("CRR")
        ax.legend(leg)
        ax.set_title("Коэффициент удержания клиентов (Customer Retention Rate, CRR) по годам для некоторых врачей")
        plt.show()


