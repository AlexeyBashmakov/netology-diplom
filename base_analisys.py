"""
базовый анализ данных полученных после первичного анализа
файл to_base_statistics.csv содержит следующую информацию:
 * client_cod - код пациента, целочисленный тип,
 * date - дата приема, тип строка, надо преобразовать в datetime.date,
 * payCat - платный == 1/бесплатный == 0 прием,
 * birthday - дата рождения, тип строка, надо преобразовать в datetime.date,
 * genderCat - пол пациента: мужчина == 1, женщина == 0,
 * insurerCat - код страховой, целочисленная категория, но т.к. имеются пропуски python читает как вещественный тип,
 * ind_codeCat - код врача, целочисленная категория,
 * diag_codeCat - код диагноза, целочисленная категория
т.е. каждая строка файла это информация о приеме отдельного пациента
преобразования кодов страховой, врача и диагноза находятся в файле prior_analisys_datas.py

что можно сделать простого:
 + процентное соотношение мужчин и женщин среди пациентов
 + возрастное распределение
 + динамика количества приемов во времени, здесь же можно отдельно платные, бесплатные приемы
 + распределение по страховым
 + распределение по врачам (гистограмма)
   + распределение количества приемов во времени, в разрезе врачей, можно выделить и исключить врачей с малым количеством приемов
 - распределение диагнозов ??? их много, наверно не стоит
 - здесь уже можно посчитать эту метрику (Коэффициент удержания клиентов, (Customer Retention Rate, CRR)):
                                                            количество уникальных пациентов бывших у этого врача больше одного раза
процент возвращающихся пациентов для конкретного врача = -----------------------------------------------------------------------------
                                                                           количество уникальных пациентов этого врача
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

def gender_age_distribution(DF):
    """
    Функция строит возрастные распределения
    """
    print("Соотношение мужчин и женщин")
    gender_proportional = DF[(DF.age > 17) & (DF.age < 90)][["client_cod", "genderCat"]].groupby("genderCat").count()
    # я сгруппировал по полу, поэтому получился индекс: 0 - женщины, 1 - мужчины
    print(f"Мужчин: {gender_proportional.loc[1, 'client_cod']:6} человек, {gender_proportional.loc[1, 'client_cod'] / gender_proportional['client_cod'].sum() * 100:.3}%")
    print(f"Женщин: {gender_proportional.loc[0, 'client_cod']:6} человек, {gender_proportional.loc[0, 'client_cod'] / gender_proportional['client_cod'].sum() * 100:.3}%")

    # строю гистограммы распределения пациентов по возрасту
    # ограничиваю себя диапазоном от 17 до 90 лет
    df_small = DF[(DF.age > 17) & (DF.age < 90)].drop_duplicates(["client_cod", "genderCat", "age"])
    weight = len(df_small)
    weight0 = len(df_small[df_small["genderCat"] == 0])
    weight1 = len(df_small[df_small["genderCat"] == 1])
    bins_ = 70
    df_small["age"].plot.hist(bins = bins_, alpha = 0.5, weights = [1./weight]*weight, color = "b")
    df_small[df_small["genderCat"] == 0]["age"].plot.hist(bins = bins_, alpha = 0.5, weights = [1./weight0]*weight0, color = "r")
    df_small[df_small["genderCat"] == 1]["age"].plot.hist(bins = bins_, legend = False, grid = True, alpha = 0.5, weights = [1./weight1]*weight1, color = "g")
    # средние построил, но информацию не несут особо, убрал
    #plt.axvline(df_small["age"].mean(), color = "blue", alpha = 0.8, linestyle = "dashed")
    #plt.axvline(df_small[df_small["genderCat"] == 0]["age"].mean(), color = "red", alpha = 0.8, linestyle = "dashed")
    #plt.axvline(df_small[df_small["genderCat"] == 1]["age"].mean(), color = "green", alpha = 0.8, linestyle = "dashed")
    plt.legend(["совокупное", "женщины", "мужчины"])
    plt.xlabel("Возраст")
    plt.ylabel("Доля")
    plt.title("Распределение пациентов по возрасту")
    plt.show()
    """
    Выводы из распределений:
    за стоматологической помощью больше обращается людей работоспособного возраста
    """

def payed_distribution(DF):
    """
    Функция строит динамику платных и бесплатных приемов
    """
    # распределение количества приемов во времени, здесь же можно отдельно платные, бесплатные приемы
    DF["dateYM"] = DF["date"].apply(str_to_date, y = 1)

    # динамика суммарного количества приемов, решил опустить, т.к. это сумма отдельных, которые вместе строю ниже
    #priems_by_date = DF[["client_cod", "dateYM"]].groupby("dateYM").count()
    #ticks_ = list()
    #labels_ = list()
    #month_Name = lambda x: "Янв" if x == 1 else "Июль"
    #for i, m in enumerate(priems_by_date.index):
    #    if m.month == 1 or m.month ==7:
    #        ticks_.append(i)
    #        labels_.append(f"{month_Name(m.month)}/{m.year-2000}")
    #priems_by_date.plot.bar(xlabel = "Дата", ylabel = "Количество приемов", legend = False, grid = True)
    #plt.title("Количество приемов по месяцам")
    #plt.xticks(ticks = ticks_, labels = labels_, rotation = 45)
    #plt.show()

    payed0 = DF[DF.payCat == 0][["client_cod", "dateYM"]].groupby("dateYM").count()
    payed0.columns = ["non_pay"]
    payed1 = DF[DF.payCat == 1][["client_cod", "dateYM"]].groupby("dateYM").count()
    payed1.columns = ["pay"]
    payed = pd.merge(payed0, payed1, how = "inner", left_on = "dateYM", right_on = "dateYM")
    ticks_ = list()
    labels_ = list()
    month_Name = lambda x: "Янв" if x == 1 else "Июль"
    for i, m in enumerate(payed.index):
        if m.month == 1 or m.month ==7:
            ticks_.append(i)
            labels_.append(f"{month_Name(m.month)}/{m.year-2000}")
    payed.plot.bar(xlabel = "Дата", ylabel = "Количество приемов", legend = True, grid = True)
    plt.xticks(ticks = ticks_, labels = labels_, rotation = 45)
    plt.legend(["бесплатные", "платные"])
    plt.title("Количество приемов по месяцам")
    plt.show()
    """
    Выводы из распределений:
    1. в 2017, 2019, 2020 и первой половине 2021 года количество бесплатных и платных приемов сопоставимо,
       в другое время количество платных приемов в разы превышает количество бесплатных приемов
    2. со второй половины 2015 года существенное увеличение числа платных приемов,
       возможная причина - накопление базы пациентов, клиника стала узнаваемой
    3. по платным приемам: локальные спады в августе-сентябре и декабре, первый, возможно, из-за завершения периода отпусков
       и начала учебного года (и подготовки к нему), второй, возможно, из-за подготовки к празднованию Нового года
    """

def insurers_distribution(DF):
    """
    Функция строит распределение приемов по страховым
    """
    # берем записи только со страховой
    on_insurers = DF[~DF.insurerCat.isna()][["client_cod", "insurerCat", "D"]]
    # столбец с кодом страховой преобразую в целый тип
    on_insurers["insurerCat"] = on_insurers["insurerCat"].astype("Int64")
    # считаем полное количество приемов по каждой страховой
    ins_f = on_insurers[["client_cod", "insurerCat"]].groupby("insurerCat").count()
    ins_f.columns = ["full"]
    # считаем количество приемов по каждой страховой за 2022 год
    ins_2 = on_insurers[on_insurers["D"] > dt.date(2021, 12, 31)][["client_cod", "insurerCat"]].groupby("insurerCat").count()
    ins_2.columns = ["2022"]
    # считаем количество приемов по каждой страховой за 2021 год
    ins_1 = on_insurers[(on_insurers["D"] > dt.date(2020, 12, 31)) & (on_insurers["D"] < dt.date(2022, 1, 1))][["client_cod", "insurerCat"]].groupby("insurerCat").count()
    ins_1.columns = ["2021"]
    insurers = pd.merge(ins_1/ins_1.sum()[0], ins_f/ins_f.sum()[0], how = "inner", left_on = "insurerCat", right_on = "insurerCat")
    insurers = insurers.merge(ins_2/ins_2.sum()[0], on = "insurerCat")
    insurers.plot.bar(rot = 0, xlabel = "Код страховой", ylabel = "Доля приемов", grid = True)
    plt.legend(["2021 год", "все года", "2022 год"])
    plt.title("Доля приемов по каждой страховой")
    plt.show()
    """
    Выводы из распределений:
    наибольшее количество приемов у страховой с кодом 0, затем, не сильно меньше, у страховой с кодом 1
    у остальных страховых существенно меньше количество приемов
    """

def doctors_distribution(DF):
    """
    Функция строит распределение количества дней отработанных врачом и принятых им пациентов
    """
    # распределение приемов по врачам
    doctors = DF[["client_cod", "ind_codeCat", "D"]]
    # начало работы каждого врача
    d_begin_work = doctors[["ind_codeCat", "D"]].groupby("ind_codeCat").min().sort_values("D", ascending = True)
    # окончание работы каждого врача
    d_end_work = doctors[["ind_codeCat", "D"]].groupby("ind_codeCat").max().sort_values("D", ascending = True)
    d_work = pd.merge(d_begin_work, d_end_work, on = "ind_codeCat")
    d_work.columns = ["begin", "end"]
    # продолжительность работы каждого врача
    d_work["period, days"] = d_work["end"] - d_work["begin"]
    # из типа datetime.timedelta перевожу в Int64
    d_work["period, days"] = d_work["period, days"].apply(lambda x: x.days)
    d_work.sort_values("period, days", ascending = False, inplace = True)
    # количество пациентов каждого врача
    d_patients = doctors[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count()
    d_work = d_work.merge(d_patients, on = "ind_codeCat")
    d_work.columns = list(d_work.columns[:-1]) + ["patients"]
    # количество пациентов врача в день, оказалась вообще не показательная метрика
    #d_work["pat on day"] = d_work["patients"]/d_work["period, days"]
    # оставил врачей проработавших дольше начала 2016 года, больше 100 дней и принявших больше 100 пациентов (да, такие есть)
    d_work = d_work[(d_work["end"] > dt.date(2015, 12, 31)) & (d_work["period, days"] > 100) & (d_work["patients"] > 100)]
    #d_work[["period, days", "patients"]].plot.bar(rot = 0, xlabel = "Код врача", ylabel = "Количество ", grid = True)
    #plt.legend(["отработанные дни", "принятые пациенты"])
    #plt.title("Количество дней проработанных и пациентов принятых врачом")
    #plt.show()
    
    # через внутреннее соединение со списком врачей, оставленных для анализа, в датафрейме с приемами оставил только интересующие строчки
    # reset_index() - для перевода ind_codeCat из индекса в столбец
    # reset_index(drop = True) - чтобы после соединения индекс датафрейма был последовательный
    #doctors = doctors.merge(d_work.reset_index()["ind_codeCat"], on = "ind_codeCat").reset_index(drop = True)
    
    #print(d_work.info())
    return d_work.reset_index()["ind_codeCat"]
    
    """
    Выводы:
    ничего конкретного не могу сказать, т.к. врачи работают и разное количество времени и принимают разное количество пациентов
    """


print("Загрузка данных подготовленных для базовой статистики")
DF = pd.read_csv("to_base_statistics.csv")
print(DF.info())

# для возрастного распределения нужно посчитать количество полных лет каждого пациента
#mL = list(map(int, input().split()))
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

#gender_age_distribution(DF)
#payed_distribution(DF)
#insurers_distribution(DF)
doctors = doctors_distribution(DF)
DF = DF.merge(doctors, on = "ind_codeCat").reset_index(drop = True)
#print(type(doctors))


#                                                             количество уникальных пациентов бывших у этого врача больше одного раза
# процент возвращающихся пациентов для конкретного врача = -----------------------------------------------------------------------------
#                                                                            количество уникальных пациентов этого врача

#print(DF.info())


#print(DF.ind_codeCat.unique())
# коды врачей заменю другим целым числом, потому что сейчас коды не идут последовательно
# сначала создадим словарь сопоставляющий каждому уникальному коду врача целое число
ind_code = dict()
# в цикле его заполним
for i, code in enumerate(DF.ind_codeCat.unique()):
    # в словаре уникальный код врача это ключ для целого числа
    ind_code[code] = i
# создаем столбец с помощью лямбда функции, которая просто возвращает целое число из словаря по коду врача
DF.loc[:, "ind_codeCat"] = DF["ind_codeCat"].apply(lambda c: ind_code[c])

# количество уникальных пациентов каждого врача
#print(DF[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").value_counts())
# получил датафрейм, в каждой строчке которого записано какой пациент у какого врача сколько раз был
#df_ = DF[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").value_counts().reset_index()
# предыдущая и следующая строки дают одинаковые датафреймы, но с разным порядком столбцов и строк
df = DF[["client_cod", "ind_codeCat"]].value_counts(["client_cod", "ind_codeCat"]).reset_index()
df.columns = list(df.columns[:-1]) + ["priems"]
#print(df_.info())
#print(df.info())
df = pd.merge(df[["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count(), \
         df[df.priems > 1][["client_cod", "ind_codeCat"]].groupby("ind_codeCat").count(), \
         on = "ind_codeCat").reset_index()
df.columns = ["ind_codeCat", "all_unique", "repeat"]
df["percent"] = df["repeat"]/df["all_unique"]
print(df)
#df["percent"].plot.bar(rot = 0, xlabel = "Код врача", ylabel = "Процент ", grid = True)
#plt.title("Процент возвращающихся пациентов для каждого врача")
#plt.show()
"""
метрика процента показала, что за все время работы стоматологии из врачей принятых в рассмотрение
минимальный процент возвращающихся пациентов больше 16,
максимальный процент - 47
"""

print(DF.info())


