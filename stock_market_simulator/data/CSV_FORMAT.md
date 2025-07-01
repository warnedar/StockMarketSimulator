Historical price CSVs stored in `data/local_csv` use a consistent six column layout.

```
Date,Open,High,Low,Close,Volume
2023-01-02,130.0,133.0,129.0,132.5,123456789
```

The first row contains the column headers exactly as shown above.  Each subsequent
row represents one trading day.  Files with other headers should be removed or
converted before running the simulator so that `load_historical_data` can read
them without special handling.
