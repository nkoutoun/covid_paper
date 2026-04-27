# Belgium COVID-19 — Replication Data

[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fj.jmacro.2025.103677-orange)](https://doi.org/10.1016/j.jmacro.2025.103677)

Replication data accompanying:

> De Schryder, S., Koutounidis, N., Schoors, K., & Weytjens, J. (2025).
> *Assessing the Heterogeneous Impact of COVID-19 on Consumption Using Bank Transactions.*
> **Journal of Macroeconomics** 84:103677.
> [doi:10.1016/j.jmacro.2025.103677](https://doi.org/10.1016/j.jmacro.2025.103677)

The double-demeaning estimator developed in the paper is published as a
separate Python package: [`ddinteract`](https://pypi.org/project/ddinteract/).

An interactive choropleth of the municipality-level data is available at
[nikolaoskoutounidis.com/html/covid_belgium_dashboard.html](https://www.nikolaoskoutounidis.com/html/covid_belgium_dashboard.html).

## Repository contents

```
data/
  intermediate_data_covid_gri.csv   Municipality × week panel (~91K rows, 36 cols)
  si_be_muni_daily.xlsx             Municipal Stringency Index methodology + raw flags
  population_by_NIS.xlsx            Population counts by NIS code (2019)
  README.md                         Detailed documentation of the SI dataset

data_public/
  municipalities/                   Pre-aggregated 581-municipality shapefile (StatBel 2019)
```

## Data sources

| Source                 | Provider                                       | Notes                                                |
| ---------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| COVID-19 cases         | Sciensano                                      | Counts < 5 per municipality/day are set to 1 for privacy |
| Vaccination            | Sciensano                                      | Municipality-level coverage                          |
| Government response    | Oxford COVID-19 Government Response Tracker    | Stringency Index, downscaled to municipalities       |
| Geographic boundaries  | StatBel                                        | Pre-aggregated from sectors to 581 municipalities    |

The municipal Stringency Index series is novel to this paper. See
[`data/README.md`](data/README.md) for the methodology.

## Citation

```bibtex
@article{deschryder2025covid,
  title   = {Assessing the Heterogeneous Impact of COVID-19 on Consumption Using Bank Transactions},
  author  = {De Schryder, Selien and Koutounidis, Nikolaos and Schoors, Koen and Weytjens, Jonas},
  journal = {Journal of Macroeconomics},
  volume  = {84},
  pages   = {103677},
  year    = {2025},
  doi     = {10.1016/j.jmacro.2025.103677}
}
```

## Contact

Maintained by **Nikolaos Koutounidis** (Ghent University). For questions about
the data or methodology, please open an issue or get in touch.
