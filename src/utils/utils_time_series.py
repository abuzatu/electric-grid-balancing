"""Module for time series cross validation: ML training, or measure rolling correlation.

Regular k-fold validation does not work as you also train in data that happens
after the test data, leading to data leakage.

If we want to train a ML model, or even to measure correlations of two time series,
we want to do it in splits while preserving the order of the elements.

There are two ways of doing time-series cross-validation:
* rolling-window
* walk forward

Both can be coded with `sklearn.model_selection.TimeSeriesSplit`,
but we build wrappers around it to be safe and easy to build.

We want to ensure more data in train than in test.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from typing import Optional, Tuple


def calculate_inputs_to_time_series_split(
    num_samples: int,
    max_train_size: Optional[int],
    test_size: int,
    rolling_window_fraction_threshold: float,
    do_print: bool,
) -> Tuple[int, Optional[int], int]:
    """Calculate inputs to time series split.

    num_samples is the length of the data frame

    max_train_size = None for rolling-window time-series cross-validation
    - and train size start from the beginning of the dataset and continues expanding
    max_train_size = is the train size after it stabilizes
    for walk-forward cross-validation

    test_size = how many samples should always be in the test sample

    rolling_window_fraction_threshold: in case we want to accept for the rolling-window
    that the train window can also be smaller than the test window,
    in this function we also ensure the train size is
    always equal or larger to the rolling_window_fraction_threshold * of the test size,
    so we calculate the number of splits for these edge cases too.
    """
    ratio = num_samples / test_size
    int_ratio = int(ratio)
    remainder = (ratio - int_ratio) * test_size
    remainder_fraction_of_test_size = remainder / test_size
    remainder_fraction_of_max_train_size = (
        0.0 if max_train_size is None else remainder / max_train_size
    )
    if do_print:
        print(
            f"ratio={ratio:.2f}, int_ratio={int_ratio}, remainder={remainder:.2f}, "
            f"remainder_fraction_of_test_size={remainder_fraction_of_test_size:.2f}, "
            "remainder_fraction_of_max_train_size="
            f"{remainder_fraction_of_max_train_size:.2f}"
        )
    if max_train_size is None:
        # rolling-window
        n_splits = (
            int_ratio
            if remainder_fraction_of_test_size > rolling_window_fraction_threshold
            else int_ratio - 1
        )
    else:
        # walk-forward
        if max_train_size < test_size:
            raise RuntimeError(
                f"test_size={test_size} > max_train_size={max_train_size}, "
                "not allowed for forward-walk cross-validation."
            )
        n_splits = int_ratio - int(max_train_size / test_size)
        # n_splits = int_ratio -1 if remainder_fraction_of_max_train_size>0.5
        # else int_ratio - 2
    if n_splits < 2:
        raise RuntimeError(
            f"test_size={test_size} is too large and we create n_split={n_splits}<2, "
            "and we need at least 2 splits to create a cross-validation."
        )
    if do_print:
        print(
            f"test_size={test_size}, max_train_size={max_train_size}, n_splits={n_splits}"
        )

    return n_splits, max_train_size, test_size


# illustrate the splits that are obtained
def illustrate_splits_obtained(df: pd.DataFrame, tscv: TimeSeriesSplit) -> None:
    """Illustrate the splits obtained."""
    # split the data frame using this approach and show which indices (dates) are used
    for i, (train_index, test_index) in enumerate(tscv.split(df)):
        train = df.iloc[train_index]
        test = df.iloc[test_index]
        print(
            f"i={str(i).zfill(2)}, "
            f"train={train.index.min().date()} to {train.index.max().date()} "
            f"for {len(train):-3} days, "
            f"test={test.index.min().date()} to {test.index.max().date()} "
            f"for {len(test)} days,"
        )
        # do something with the train and test sets
        pass


def create_dummy_time_series_df() -> pd.DataFrame:
    """Create a dummy time series dataframe.

    With date for every day of one year.
    """
    # Create a date range from January 1 to December 31 of a particular year
    date_range = pd.date_range(start="2022-01-01", end="2022-12-31", freq="D")
    # Create a pandas DataFrame with the date range as the index and some random values
    df = pd.DataFrame({"value": np.random.randn(len(date_range))}, index=date_range)
    # return
    return df


def test_rolling_window_time_series_cross_validation() -> None:
    """Test the rolling-window time_series cross-validation (rw_ts_cv)."""
    print("Examle of rolling-window time_series cross-validation (rw_ts_cv):")
    df = create_dummy_time_series_df()
    # test_size=30 days
    n_splits, max_train_size, test_size = calculate_inputs_to_time_series_split(
        num_samples=len(df),
        max_train_size=None,  # rolling-window time-series cross-validation
        test_size=30,
        rolling_window_fraction_threshold=0.7,
        do_print=True,
    )
    # rolling-window time-series cross-validation (rw_ts_cv)
    rw_ts_cv = TimeSeriesSplit(
        n_splits=n_splits, max_train_size=max_train_size, test_size=test_size
    )
    print(f"rw_ts_cv={rw_ts_cv}")
    illustrate_splits_obtained(df, rw_ts_cv)


def test_walk_forward_time_series_cross_validation() -> None:
    """Test the walk-forward time-series cross-validation (wf_ts_cv)."""
    print("Example of walk-forward time-series cross-validation (wf_ts_cv):")
    df = create_dummy_time_series_df()
    # train_size = 60 days, test_size = 30 days
    n_splits, max_train_size, test_size = calculate_inputs_to_time_series_split(
        num_samples=len(df),
        max_train_size=60,  # walk-forward time-series cross-validation
        test_size=30,
        rolling_window_fraction_threshold=0.7,
        do_print=True,
    )
    # walk-forward time-series cross-validation (wf_ts_cv)
    wf_ts_cv = TimeSeriesSplit(
        n_splits=n_splits, max_train_size=max_train_size, test_size=test_size
    )
    print(f"wf_ts_cv={wf_ts_cv}")
    illustrate_splits_obtained(df, wf_ts_cv)


"""Class to check if there are missing data in the time series."""


class CheckMissingDates:
    """Class CheckMissingDates."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        if "datetime" not in self.df.columns:
            raise ValueError("Column 'datetime' not found in the dataframe.")

    def fit(self) -> None:
        self.check_missing_dates()

    def check_missing_dates(self) -> None:
        """Check if there are missing dates in the time series."""
        # Assuming df is your DataFrame
        first_date = self.df["datetime"].min()
        last_date = self.df["datetime"].max()

        # Create a date range for all weekdays between the first and last date
        self.all_weekdays = pd.date_range(start=first_date, end=last_date, freq="B")
        # Create a date range for all Tuesdays between the first and last date
        self.all_tuesdays = pd.date_range(start=first_date, end=last_date, freq="W-TUE")
        # extract all dates in the dataframe
        self.all_dates_in_df = self.df["datetime"].unique()

        # sets
        self.set_all_weekdays = set(self.all_weekdays)
        self.set_all_tuesdays = set(self.all_tuesdays)
        self.set_all_dates_in_df = set(self.all_dates_in_df)

        # check if all dates in the dataframe are in the all_weekdays
        # Find missing weekdays by comparing the sets
        self.set_missing_weekdays = self.set_all_weekdays - self.set_all_dates_in_df
        # print(f"Missing {len(self.set_missing_weekdays)} weekdays")
        # check if missing Tuesdays
        self.set_missing_tuesdays = self.set_all_tuesdays - self.set_all_dates_in_df
        # print(f"Missing {len(self.set_missing_tuesdays)} Tuesdays")
        self.list_missing_weekdays = [
            (missing_weekday, missing_weekday.weekday())
            for missing_weekday in sorted(self.set_missing_weekdays)
        ]
        print(f"Missing {len(self.list_missing_weekdays)} weekdays")
        for missing_weekday in self.list_missing_weekdays:
            print(f"  {missing_weekday}")
        self.list_missing_tuesdays = [
            (missing_tuesday, missing_tuesday.weekday())
            for missing_tuesday in sorted(self.set_missing_tuesdays)
        ]
        print(f"Missing {len(self.list_missing_tuesdays)} Tuesdays")
        for missing_tuesday in self.list_missing_tuesdays:
            print(f"  {missing_tuesday}")
