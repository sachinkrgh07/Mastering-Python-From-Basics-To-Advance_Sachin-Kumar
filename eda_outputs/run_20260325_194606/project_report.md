# Data Analytics Project Report

Source: `c:\Users\ashok\Desktop\TEST\dmd_fixed\portable_accounts.db`

## Task 1: Data Understanding
- Shape: (360, 8)
- Columns: ['Flow', 'Sales', 'Profit', 'Quantity', 'Price', 'Items', 'Category', 'Date']
- Mapped Columns: {'Sales': 'amount', 'Profit': None, 'Quantity': None, 'Price': None, 'Items': 'description', 'Category': None, 'Date': 'date', 'Flow': 'flow'}
- Date Range Used: Full date span used.

### First 5 Rows
| Flow   |    Sales |   Profit |   Quantity |    Price | Items                                                                                                           | Category   | Date                |
|:-------|---------:|---------:|-----------:|---------:|:----------------------------------------------------------------------------------------------------------------|:-----------|:--------------------|
| IN     |  22496.3 |  22496.3 |          1 |  22496.3 | Bookshelf Tall(1x10093.1), TV Unit 5ft(1x11331.94) | Tax:5%                                                     | IN         | 2025-09-14 00:00:00 |
| IN     | 135425   | 135425   |          1 | 135425   | King Bed(1x33288.45), Meeting Table(2x29921.97), Partition Panel(3x6151.24), Bedside Table(2x4664.46) | Tax:12% | IN         | 2026-01-18 00:00:00 |
| IN     | 112872   | 112872   |          1 | 112872   | L Shape Sofa(1x51136.52), Folding Table(4x2660.27), Baby Cot(3x12881.38) | Tax:12% | Frgt:400                   | IN         | 2025-11-22 00:00:00 |
| IN     | 173795   | 173795   |          1 | 173795   | Center Table(4x7881.46), King Bed(3x29196.46), TV Unit 5ft(3x11826.14) | Tax:12% | Frgt:650                     | IN         | 2026-02-13 00:00:00 |
| IN     |  76704.6 |  76704.6 |          1 |  76704.6 | Dining Table 4 Seater(4x17652.75), Folding Table(2x3046.78)                                                     | IN         | 2026-01-29 00:00:00 |

### Last 5 Rows
| Flow   |    Sales |   Profit |   Quantity |    Price | Items                                                                                                 | Category   | Date                |
|:-------|---------:|---------:|-----------:|---------:|:------------------------------------------------------------------------------------------------------|:-----------|:--------------------|
| IN     | 127757   | 127757   |          1 | 127757   | Mirror Frame(4x3095.05), Dining Table 4 Seater(3x18786.73), Baby Cot(3x12921.83) | Tax:18% | Frgt:900 | IN         | 2026-03-07 00:00:00 |
| OUT    |      0   | -93207.6 |          1 |      0   | Display Cabinet(2x21910.06), Baby Cot(3x11652.5) | Tax:18% | Frgt:250                                 | OUT        | 2025-12-05 00:00:00 |
| OUT    |      0   | -72410.5 |          1 |      0   | Bunk Bed(2x32326.11) | Tax:12%                                                                        | OUT        | 2025-08-17 00:00:00 |
| IN     | 111003   | 111003   |          1 | 111003   | Kitchen Cabinet(2x17402.05), Rocking Chair(4x7043.36), Display Cabinet(2x21370.03) | Tax:5%           | IN         | 2025-10-12 00:00:00 |
| IN     |  41928.9 |  41928.9 |          1 |  41928.9 | Coffee Table(4x6472.47), Dresser Unit(1x11546.65) | Tax:12%                                           | IN         | 2026-03-12 00:00:00 |

### Data Type Classification
- quantitative_discrete: ['Quantity']
- quantitative_continuous: ['Sales', 'Profit', 'Price']
- qualitative_nominal: ['Items', 'Date']
- qualitative_ordinal: ['Flow', 'Category']

## Task 2: EDA
- Plots are consolidated into PDF: `eda_plots.pdf`

### Correlation Matrix
|          |      Sales |     Profit |   Quantity |      Price |
|:---------|-----------:|-----------:|-----------:|-----------:|
| Sales    |   1        |   0.886242 |        nan |   1        |
| Profit   |   0.886242 |   1        |        nan |   0.886242 |
| Quantity | nan        | nan        |        nan | nan        |
| Price    |   1        |   0.886242 |        nan |   1        |

## Task 3: Missing Data and Outliers
### Missing Values
|          |   missing_count |
|:---------|----------------:|
| Flow     |               0 |
| Sales    |               0 |
| Profit   |               0 |
| Quantity |               0 |
| Price    |               0 |
| Items    |               0 |
| Category |               0 |
| Date     |               0 |

### Outlier Counts (IQR Method)
- Sales: 8
- Profit: 1
- Quantity: 0
- Price: 8

Impact of outliers: extreme values can pull mean/regression slope and reduce model generalization.

## Task 4: Spread of Data
| variable   |    mean |   median |      std |   skewness |   kurtosis | distribution         |
|:-----------|--------:|---------:|---------:|-----------:|-----------:|:---------------------|
| Sales      | 60896   |  29579.8 |  73515.2 |   1.16949  |   0.50783  | Right Skewed         |
| Profit     | 25038.7 |  29579.8 | 116560   |  -0.179901 |  -0.102149 | Approximately Normal |
| Quantity   |     1   |      1   |      0   |   0        |   0        | Approximately Normal |
| Price      | 60896   |  29579.8 |  73515.2 |   1.16949  |   0.50783  | Right Skewed         |

## Task 5: Automated EDA
### describe()
|          |   count |   unique | top                                                         |   freq | mean                | min                 | 25%                 | 50%                 | 75%                 | max                 |      std |
|:---------|--------:|---------:|:------------------------------------------------------------|-------:|:--------------------|:--------------------|:--------------------|:--------------------|:--------------------|:--------------------|---------:|
| Flow     |     360 |        2 | IN                                                          |    226 | nan                 | nan                 | nan                 | nan                 | nan                 | nan                 |    nan   |
| Sales    |     360 |      nan | nan                                                         |    nan | 60895.98519444445   | 0.0                 | 0.0                 | 29579.800000000003  | 101745.5175         | 298237.47           |  73515.2 |
| Profit   |     360 |      nan | nan                                                         |    nan | 25038.737527777776  | -398797.79          | -59147.505000000005 | 29579.800000000003  | 101745.5175         | 298237.47           | 116560   |
| Quantity |     360 |      nan | nan                                                         |    nan | 1.0                 | 1.0                 | 1.0                 | 1.0                 | 1.0                 | 1.0                 |      0   |
| Price    |     360 |      nan | nan                                                         |    nan | 60895.98519444445   | 0.0                 | 0.0                 | 29579.800000000003  | 101745.5175         | 298237.47           |  73515.2 |
| Items    |     360 |      360 | Bookshelf Tall(1x10093.1), TV Unit 5ft(1x11331.94) | Tax:5% |      1 | nan                 | nan                 | nan                 | nan                 | nan                 | nan                 |    nan   |
| Category |     360 |        2 | IN                                                          |    226 | nan                 | nan                 | nan                 | nan                 | nan                 | nan                 |    nan   |
| Date     |     360 |      nan | nan                                                         |    nan | 2025-12-07 13:56:00 | 2025-08-17 00:00:00 | 2025-10-14 00:00:00 | 2025-12-09 12:00:00 | 2026-01-27 12:00:00 | 2026-03-24 00:00:00 |    nan   |

### info()

```<class 'pandas.DataFrame'>
RangeIndex: 360 entries, 0 to 359
Data columns (total 8 columns):
 #   Column    Non-Null Count  Dtype         
---  ------    --------------  -----         
 0   Flow      360 non-null    str           
 1   Sales     360 non-null    float64       
 2   Profit    360 non-null    float64       
 3   Quantity  360 non-null    float64       
 4   Price     360 non-null    float64       
 5   Items     360 non-null    str           
 6   Category  360 non-null    str           
 7   Date      360 non-null    datetime64[us]
dtypes: datetime64[us](1), float64(4), str(3)
memory usage: 51.6 KB
```

### isnull()
|          |   missing_count |
|:---------|----------------:|
| Flow     |               0 |
| Sales    |               0 |
| Profit   |               0 |
| Quantity |               0 |
| Price    |               0 |
| Items    |               0 |
| Category |               0 |
| Date     |               0 |

### corr()
|          |      Sales |     Profit |   Quantity |      Price |
|:---------|-----------:|-----------:|-----------:|-----------:|
| Sales    |   1        |   0.886242 |        nan |   1        |
| Profit   |   0.886242 |   1        |        nan |   0.886242 |
| Quantity | nan        | nan        |        nan | nan        |
| Price    |   1        |   0.886242 |        nan |   1        |

## Task 6: Regression Analysis
- Dependent variable: Sales
- Independent variables: Quantity, Price, Flow_IN

### Covariance
|          |           Sales |   Quantity |           Price |      Flow_IN |
|:---------|----------------:|-----------:|----------------:|-------------:|
| Sales    |     5.40448e+09 |          0 |     5.40448e+09 | 22730        |
| Quantity |     0           |          0 |     0           |     0        |
| Price    |     5.40448e+09 |          0 |     5.40448e+09 | 22730        |
| Flow_IN  | 22730           |          0 | 22730           |     0.234324 |

### Correlation
|          |      Sales |   Quantity |      Price |    Flow_IN |
|:---------|-----------:|-----------:|-----------:|-----------:|
| Sales    |   1        |        nan |   1        |   0.638725 |
| Quantity | nan        |        nan | nan        | nan        |
| Price    |   1        |        nan |   1        |   0.638725 |
| Flow_IN  |   0.638725 |        nan |   0.638725 |   1        |

## Task 7: Supervised Learning Models
### (i) Simple Linear Regression
- Train: {'MSE': 5797781151.327026, 'MAE': 62574.75889446159, 'R2': 0.0}
- Validation: {'MSE': 5062656076.303416, 'MAE': 58451.6362191358, 'R2': -0.009450551459240453}
- Test: {'MSE': 4521472230.54784, 'MAE': 58425.98528935186, 'R2': -0.006473964032785107}

### (ii) Multi Linear Regression
- Train: {'MSE': 3.35599811994344e-22, 'MAE': 1.2812927673588059e-11, 'R2': 1.0}
- Validation: {'MSE': 2.409450749551163e-22, 'MAE': 1.176027176875828e-11, 'R2': 1.0}
- Test: {'MSE': 2.361859142780317e-22, 'MAE': 1.16655327373236e-11, 'R2': 1.0}

### (iii) Logistic Regression
- Accuracy: 1.0000
- Confusion Matrix:
[[37  0]
 [ 0 53]]

## Task 9: Overfitting / Underfitting
|   degree |   train_mse |    test_mse |
|---------:|------------:|------------:|
|        1 | 5.74826e+09 | 4.58123e+09 |
|        2 | 5.74826e+09 | 4.58123e+09 |
|        3 | 5.74826e+09 | 4.58123e+09 |
|        5 | 5.74826e+09 | 4.58123e+09 |

As degree increases, train error may reduce while test error may rise (overfitting).

## Task 10: Classification Task
- Converted target: Profit > 0 => Profitable (1), else Not Profitable (0).
- Accuracy: 1.0000
- Confusion Matrix:
[[37  0]
 [ 0 53]]

## Task 11 & 12: Model Evaluation
- Simple Regression Test Metrics: {'MSE': 4521472230.54784, 'MAE': 58425.98528935186, 'R2': -0.006473964032785107}
- Multi Regression Test Metrics: {'MSE': 2.361859142780317e-22, 'MAE': 1.16655327373236e-11, 'R2': 1.0}
- Classification Accuracy: 1.0000

## Task 13: Data Visualization
- All plots are saved in a single PDF file: `eda_plots.pdf`
- Temporary PNG plot files are deleted after PDF creation.
