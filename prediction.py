"""
Построение модели классификации для прогнозирования будущего возвращения пациента
ФОМС каждый новый год каждого пациента считает как нового
Врачи увольняются, их пациенты переходят к другим врачам
Вижу такие варианты модели прогнозирования:
1) прогнозирование в рамках одного (каждого) года
2) прогнозирование на первую половину 2022 года на основе данных за 2014-2021 года
"""

import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from crr import load_and_prepare

DF = load_and_prepare()
DF = DF[DF.D > dt.date(2013, 12, 31)].reset_index(drop = True)
print(DF.info())
