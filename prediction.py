"""
Построение модели классификации для прогнозирования будущего возвращения пациента
ФОМС каждый новый год каждого пациента считает как нового
Врачи увольняются, их пациенты переходят к другим врачам
Вижу такие варианты модели прогнозирования:
1) прогнозирование в рамках одного (каждого) года
2) прогнозирование на первую половину 2022 года на основе данных за 2014-2021 года
"""

"""
Каждая строка в файле соответствует приему одного пациента.
Столбцы в файле csv:
1. client_cod - целочисленный код пациента
2. genderCat - пол пациента, целое число: 0 - женщина, 1 - мужчина
3. A - возраст клиента на момент приема, тип datetime.date
4. insurerCat - код страховой компании пациента: 0, 1, 2, 3, 4, nan - там где пациент не указал страховую
5. D - дата приема, тип datetime.date
6. ind_codeCat - целочисленный код врача, всего 11 от 0 до 10
7. diag_codeCat - целочисленный код диагноза, всего 70 от 0 до 75 с пропусками
8. payCat - платный = 1/бесплатный = 0 прием
"""

import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from crr import load_and_prepare

# для построения модели логистической регрессии импортируем нужное
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
# загружае функции вычисления среднеквадратичной ошибки, расчета точности и матрицы ошибок
from sklearn.metrics import mean_squared_error, accuracy_score, confusion_matrix
# импортируем LDA- и QDA-функционал
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis

from sys import stdout

def one_year_predict(x: pd.DataFrame, y: pd.Series, name_model: str = "LogisticRegression", file_ = stdout):
    """
    Функция реализует модель классификации для прогнозирования будущего возвращения пациента в течение одного года
    На вход подается датафрейм с данными одного года
    """
    # разбиваю данные для обучения и проверки
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.2, random_state = 0)
    if name_model == "LogisticRegression":
        # максимальное число итераций
        maxIter = 1000
        # создаю и обучаю модель LogisticRegression
        model = LogisticRegression(max_iter = maxIter, random_state = 0).fit(x_train, y_train)
        print("Максимальное число итераций:", maxIter, file = file_)
    elif name_model == "LogisticRegressionCV":
        # максимальное число итераций
        maxIter = 1000
        # создаю и обучаю модель LogisticRegressionCV
        model = LogisticRegressionCV(cv = 10, max_iter = maxIter, random_state = 0).fit(x_train, y_train)
        print("Максимальное число итераций:", maxIter, file = file_)
    elif name_model == "LinearDiscriminantAnalysis":
        # создаю и обучаю модель LinearDiscriminantAnalysis
        model = LinearDiscriminantAnalysis().fit(x_train, y_train)
    elif name_model == "QuadraticDiscriminantAnalysis":
        # создаю и обучаю модель QuadraticDiscriminantAnalysis
        model = QuadraticDiscriminantAnalysis().fit(x_train, y_train)
    else:
        print("Неизвестная модель!")
        return
    # предсказания модели
    model_predict_train = model.predict(x_train)
    model_predict_test = model.predict(x_test)
    # качество на обучающей выборке
    print("СКО на обучающей выборке:", mean_squared_error(y_train, model_predict_train), file = file_)
    # качество на тестовой выборке
    print("СКО на тестовой выборке :", mean_squared_error(y_test, model_predict_test), file = file_)
    # расчет точности
    print("Расчет точности:", accuracy_score(y_test, model_predict_test), file = file_)
    # матрица ошибок
    print("Матрица ошибок:\n", confusion_matrix(y_test, model_predict_test), file = file_)


# загружаю данные и готовлю
DF = load_and_prepare()
# отбрасываю 2013-й год
DF = DF[DF.D > dt.date(2013, 12, 31)].reset_index(drop = True)
#print(DF.info())
# пропущенные значения кодов страховой заменяю на целое, чтобы потом использовать в модели предсказания
DF["insurerCat"].fillna(5, inplace = True)
# тип данных в столбце меняю на целый
DF["insurerCat"] = DF["insurerCat"].astype("Int64")

"""
Надо добавить столбец с целевой переменной - вернулся пациент (1) или нет (0)
Столбец client_cod не должен быть среди признаков - это идентификатор пациента как и ФИО
"""
f = open("prediction.txt", "a")
f.write(f"{dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')}\n")
fCV = open("predictionCV.txt", "a")
fCV.write(f"{dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')}\n")
fLDA = open("predictionLDA.txt", "a")
fLDA.write(f"{dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')}\n")
fQDA = open("predictionQDA.txt", "a")
fQDA.write(f"{dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')}\n")
for i in range(2014, 2022):
    # делаю копию, чтобы не связываться с view
    DF_ = DF[(DF.D > dt.date(i-1, 12, 31)) & (DF.D < dt.date(i+1, 1, 1))].copy()
    print(f"{i} год, записей {len(DF_)}")
    f.write(f"{i} год, записей {len(DF_)}\n")
    fCV.write(f"{i} год, записей {len(DF_)}\n")
    fLDA.write(f"{i} год, записей {len(DF_)}\n")
    fQDA.write(f"{i} год, записей {len(DF_)}\n")
    # в столбце D данные имеют тип datetime.date, его надо перевести в целый или вещественный
    # для прогнозирования в рамках года, эти данные перевожу в целый тип - день года
    DF_.loc[:, "D"] = DF_["D"].apply(lambda x: (x - dt.date(x.year, 1, 1)).days)
    # для добавления столбца с целевой переменной надо составить датафрейм с идентификаторами пациентов и их количеством посещений
    df = DF_["client_cod"].value_counts().reset_index()
    df.columns = ["client_cod", "priems"]
    df["return"] = df["priems"].apply(lambda x: int(1) if x > 1 else int(0))
    DF_ = DF_.merge(df[["client_cod", "return"]], how = "inner", on = "client_cod")
    print("LogisticRegression...", end = "")
    one_year_predict(DF_[list(set(DF_.columns) - set(["client_cod", "return"]))], DF_["return"], "LogisticRegression", f)
    print("LogisticRegressionCV...", end = "")
    one_year_predict(DF_[list(set(DF_.columns) - set(["client_cod", "return"]))], DF_["return"], "LogisticRegressionCV", fCV)
    print("LinearDiscriminantAnalysis...", end = "")
    one_year_predict(DF_[list(set(DF_.columns) - set(["client_cod", "return"]))], DF_["return"], "LinearDiscriminantAnalysis", fLDA)
    print("QuadraticDiscriminantAnalysis...")
    one_year_predict(DF_[list(set(DF_.columns) - set(["client_cod", "return"]))], DF_["return"], "QuadraticDiscriminantAnalysis", fQDA)
    print()
    f.write("\n")
    fCV.write("\n")
    fLDA.write("\n")
    fQDA.write("\n")

f.close()
fCV.close()
fLDA.close()
fQDA.close()

