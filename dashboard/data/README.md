# Municipal Stringency Index Dataset

## Overview

Novel Stringency Index dataset for Belgian municipalities during COVID-19, providing daily measures of government policy stringency with extra granularity for studying heterogeneous NPI impacts.

**Publication**: **De Schryder, Selien, Nikolaos Koutounidis, Koen Schoors, and Johannes Weytjens. 2025. 'Assessing the Heterogeneous Impact of COVID-19 on Consumption Using Bank Transactions'. Journal of Macroeconomics 84:103677.**

## Methodology

**Problem**: OxCGRT provides only national-level measures, missing sub-national variation in Belgium's federal structure.

**Solution**: Two-step approach:
1. **Baseline**: Establish minimum intensive measures across Belgium using adjusted OxCGRT flags
2. **Enhancement**: Add local measures from official announcements where municipalities implemented more intensive policies

**Result**: Municipal SI values that are never less restrictive than national baseline, but can be more restrictive based on local evidence.

## Files

### **si_be_muni_daily.xlsx** (Methodology Documentation)
- **Sheet 1**: Country-wide baseline measures (minimum intensity flags)
- **Sheet 2**: Calculation formulas for baseline stringency
- **Sheet 3**: Local measures documentation and timing

### **intermediate_data_covid_gri.csv** (Analysis Data)
- **Final municipal-level Stringency Index data**
- Daily values for 581 Belgian municipalities
- Scale: 0-100 (higher = more stringent)
- Ready for empirical analysis


## Citation

```
De Schryder, S., Koutounidis, N., Schoors, K., & Weytjens, J. (2025). 
Assessing the Heterogeneous Impact of COVID-19 on Consumption Using Bank Transactions. 
Journal of Macroeconomics, 84, 103677. 
https://doi.org/10.1016/j.jmacro.2025.103677
```

---
*First comprehensive municipal-level stringency measures for Belgium, enabling precise analysis of heterogeneous policy impacts.*
