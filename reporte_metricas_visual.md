---
## Evaluación del Usuario 15 (Perfil de Alto Consumo y Alto Error)

### Usuario: 15 | Categoría: Comercio
**$n = 90$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/90) \times 4790.46$ minutos
* MAE = 53.23 minutos
* MAE = 53.23 / 60 horas
**Resultado: MAE = 0.89 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 352917.57$ minutos²
* $RMSE = \sqrt{[352917.57 / 90]}$
* $RMSE = \sqrt{[3921.31]}$
* RMSE = 62.62 minutos
* RMSE = 62.62 / 60 horas
**Resultado: RMSE = 1.04 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 150.50$ minutos
* $SS_{res} = 352917.57$ minutos²
* $SS_{tot} = 249719.01$ minutos²
* $R^2 = 1 - (352917.57 / 249719.01)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 58 (de 90 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 37.99$
* MAPE = (100 / 58) $\times$ 37.99
**Resultado: MAPE = 65.5%**

---

### Usuario: 15 | Categoría: Entretenimiento
**$n = 88$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/88) \times 9971.79$ minutos
* MAE = 113.32 minutos
* MAE = 113.32 / 60 horas
**Resultado: MAE = 1.89 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 1563959.33$ minutos²
* $RMSE = \sqrt{[1563959.33 / 88]}$
* $RMSE = \sqrt{[17772.27]}$
* RMSE = 133.31 minutos
* RMSE = 133.31 / 60 horas
**Resultado: RMSE = 2.22 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 320.40$ minutos
* $SS_{res} = 1563959.33$ minutos²
* $SS_{tot} = 1106633.40$ minutos²
* $R^2 = 1 - (1563959.33 / 1106633.40)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 57 (de 88 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 38.65$
* MAPE = (100 / 57) $\times$ 38.65
**Resultado: MAPE = 67.8%**

---

### Usuario: 15 | Categoría: Estudio
**$n = 91$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/91) \times 6777.94$ minutos
* MAE = 74.48 minutos
* MAE = 74.48 / 60 horas
**Resultado: MAE = 1.24 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 698740.47$ minutos²
* $RMSE = \sqrt{[698740.47 / 91]}$
* $RMSE = \sqrt{[7678.47]}$
* RMSE = 87.63 minutos
* RMSE = 87.63 / 60 horas
**Resultado: RMSE = 1.46 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 210.60$ minutos
* $SS_{res} = 698740.47$ minutos²
* $SS_{tot} = 494417.93$ minutos²
* $R^2 = 1 - (698740.47 / 494417.93)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 59 (de 91 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 41.36$
* MAPE = (100 / 59) $\times$ 41.36
**Resultado: MAPE = 70.1%**

---

### Usuario: 15 | Categoría: Herramientas
**$n = 89$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/89) \times 5675.23$ minutos
* MAE = 63.77 minutos
* MAE = 63.77 / 60 horas
**Resultado: MAE = 1.06 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 500886.39$ minutos²
* $RMSE = \sqrt{[500886.39 / 89]}$
* $RMSE = \sqrt{[5627.94]}$
* RMSE = 75.02 minutos
* RMSE = 75.02 / 60 horas
**Resultado: RMSE = 1.25 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 180.30$ minutos
* $SS_{res} = 500886.39$ minutos²
* $SS_{tot} = 354419.45$ minutos²
* $R^2 = 1 - (500886.39 / 354419.45)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 57 (de 89 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 41.27$
* MAPE = (100 / 57) $\times$ 41.27
**Resultado: MAPE = 72.4%**

---

### Usuario: 15 | Categoría: Productividad
**$n = 90$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/90) \times 13056.78$ minutos
* MAE = 145.08 minutos
* MAE = 145.08 / 60 horas
**Resultado: MAE = 2.42 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 2621751.90$ minutos²
* $RMSE = \sqrt{[2621751.90 / 90]}$
* $RMSE = \sqrt{[29130.58]}$
* RMSE = 170.68 minutos
* RMSE = 170.68 / 60 horas
**Resultado: RMSE = 2.84 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 410.20$ minutos
* $SS_{res} = 2621751.90$ minutos²
* $SS_{tot} = 1855111.04$ minutos²
* $R^2 = 1 - (2621751.90 / 1855111.04)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 58 (de 90 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 43.33$
* MAPE = (100 / 58) $\times$ 43.33
**Resultado: MAPE = 74.7%**

---

### Usuario: 15 | Categoría: Redes Sociales
**$n = 91$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/91) \times 9034.03$ minutos
* MAE = 99.28 minutos
* MAE = 99.28 / 60 horas
**Resultado: MAE = 1.65 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 1241320.67$ minutos²
* $RMSE = \sqrt{[1241320.67 / 91]}$
* $RMSE = \sqrt{[13640.89]}$
* RMSE = 116.79 minutos
* RMSE = 116.79 / 60 horas
**Resultado: RMSE = 1.95 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 280.70$ minutos
* $SS_{res} = 1241320.67$ minutos²
* $SS_{tot} = 878339.28$ minutos²
* $R^2 = 1 - (1241320.67 / 878339.28)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 59 (de 91 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 45.43$
* MAPE = (100 / 59) $\times$ 45.43
**Resultado: MAPE = 77.0%**

---

### Usuario: 15 | Categoría: Sin categoría
**$n = 87$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/87) \times 4027.70$ minutos
* MAE = 46.30 minutos
* MAE = 46.30 / 60 horas
**Resultado: MAE = 0.77 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 258081.17$ minutos²
* $RMSE = \sqrt{[258081.17 / 87]}$
* $RMSE = \sqrt{[2966.45]}$
* RMSE = 54.47 minutos
* RMSE = 54.47 / 60 horas
**Resultado: RMSE = 0.91 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 130.90$ minutos
* $SS_{res} = 258081.17$ minutos²
* $SS_{tot} = 182614.24$ minutos²
* $R^2 = 1 - (258081.17 / 182614.24)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 56 (de 87 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 44.41$
* MAPE = (100 / 56) $\times$ 44.41
**Resultado: MAPE = 79.3%**

---

### Usuario: 15 | Categoría: Trabajo
**$n = 91$ predicciones evaluadas**

#### 1. MAE (Mean Absolute Error)
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $MAE = (1/91) \times 11267.60$ minutos
* MAE = 123.82 minutos
* MAE = 123.82 / 60 horas
**Resultado: MAE = 2.06 horas**

#### 2. RMSE (Root Mean Squared Error)
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 1931004.93$ minutos²
* $RMSE = \sqrt{[1931004.93 / 91]}$
* $RMSE = \sqrt{[21219.83]}$
* RMSE = 145.67 minutos
* RMSE = 145.67 / 60 horas
**Resultado: RMSE = 2.43 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación)
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales)
* $\bar{y}$ = media de valores reales

**Sustitución de valores:**
* $\bar{y} = 350.10$ minutos
* $SS_{res} = 1931004.93$ minutos²
* $SS_{tot} = 1366349.19$ minutos²
* $R^2 = 1 - (1931004.93 / 1366349.19)$
* $R^2 = 1 - 1.4133$
**Resultado: $R^2$ = -0.41**

*Interpretación: Modelo es 41% peor que predecir la media*

#### 4. MAPE (Mean Absolute Percentage Error)
**Fórmula:**
$MAPE=(100/n)\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos = 59 (de 91 predicciones)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 48.14$
* MAPE = (100 / 59) $\times$ 48.14
**Resultado: MAPE = 81.6%**

---

### Usuario: 15 | Evaluación General
**$n = 717$ predicciones evaluadas en total**

#### 1. MAE (Mean Absolute Error) General
**Fórmula:**
$MAE=(1/n)\times\Sigma|y_{i}-\hat{y}_{i}|$

**Sustitución de valores:**
* $\Sigma|y_{i}-\hat{y}_{i}| = 64601.51$ minutos
* $MAE = (1/717) \times 64601.51$ minutos
* MAE = 90.10 minutos
* MAE = 90.10 / 60 horas
**Resultado: MAE = 1.50 horas**

#### 2. RMSE (Root Mean Squared Error) General
**Fórmula:**
$RMSE=\sqrt{[(1/n)\times\Sigma(y_{i}-\hat{y}_{i})^{2}]}$

**Sustitución de valores:**
* $\Sigma(y_{i}-\hat{y}_{i})^2 = 9168662.42$ minutos²
* $RMSE = \sqrt{[9168662.42 / 717]}$
* $RMSE = \sqrt{[12787.53]}$
* RMSE = 113.08 minutos
* RMSE = 113.08 / 60 horas
**Resultado: RMSE = 1.88 horas**

#### 3. $R^{2}$ (Coeficiente de Determinación) General
**Fórmula:**
$R^{2}=1-(SS_{res}/SS_{tot})$

**Donde:**
* $SS_{res}=\Sigma(y_{i}-\hat{y}_{i})^{2}$ (Suma de cuadrados residuales totales)
* $SS_{tot}=\Sigma(y_{i}-\bar{y})^{2}$ (Suma de cuadrados totales, considerando la media global $\bar{y}$)
* $\bar{y}$ = media global de valores reales = 254.76 minutos

**Sustitución de valores:**
* $SS_{res} = 9168662.42$ minutos²
* $SS_{tot} = 12913609.04$ minutos²
* $R^2 = 1 - (9168662.42 / 12913609.04)$
* $R^2 = 1 - 0.7100$
**Resultado: $R^2$ = 0.29**

*Interpretación: El modelo general es 29% mejor que predecir la media global*

#### 4. MAPE (Mean Absolute Percentage Error) General
**Fórmula:**
$MAPE=(100/n_{valido})\times\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]|$
*(Excluyendo casos donde $y_{i}=0$)*

**Sustitución de valores:**
* n válidos globales = 463 (de 717 predicciones totales)
* $\Sigma|[ (y_{i}-\hat{y}_{i})/y_{i} ]| = 340.57$
* MAPE = (100 / 463) $\times$ 340.57
* MAPE = 73.56%
**Resultado: MAPE = 73.6%**

---