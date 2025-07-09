"""Module to visualise with matplotlib."""

# python modules
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates
import pandas as pd
import seaborn as sns
from typing import Any, List, Optional, Tuple
import plotly.express as px


def plot_overlay_time_series_matplotlib(
    _df: pd.DataFrame,
    ylim: List[float],
    values: List[Tuple[str, str, str, float]],
    title: str,
    ref: str,
    list_dates_vertical_lines: List[str],
    list_horizontal_lines: Optional[List[float]] = None,
    list_horizontal_lines_2: Optional[List[float]] = None,
    do_show_ticks_every_tuesday: Optional[bool] = False,
    do_set_vertical_ticks: Optional[bool] = False,
    output_file_name: Optional[str] = None,
    do_printout: Optional[bool] = False,
) -> matplotlib.figure.Figure:
    """Plot overlay of any number of time series with matplotlib.

    ref is the column as reference to calculate correlation to.
    """

    df = _df.copy()

    # Set the figure size and create the plot
    fig, ax = plt.subplots(figsize=(40, 15))

    x = df.index

    # Set the tick locations and labels on the x-axis
    format = "%Y-%m-%d"
    date_form = matplotlib.dates.DateFormatter(format)
    ax.xaxis.set_major_formatter(date_form)
    if do_show_ticks_every_tuesday:
        # Set the locator to show ticks on every Tuesday
        ax.xaxis.set_major_locator(
            matplotlib.dates.WeekdayLocator(byweekday=1)
        )  # 1 corresponds to Tuesday
    ax.tick_params(axis="both", labelsize=25)
    plt.xticks(rotation=90)

    # Set vertical ticks
    if do_set_vertical_ticks:
        # Set vertical ticks based on horizontal line values
        vertical_ticks = (
            [-30, -20, -10, -5, 105, 110, 120, 130]
            + list_horizontal_lines
            + list_horizontal_lines_2
        )
        ax.set_yticks(vertical_ticks)

    for name, label_name, color, multiplier in values:
        s = df[name].map(lambda x: x)
        if ref is not None:
            correlation = s.corr(df[ref])
            label_name = f"{label_name}, corr={correlation:.3f}"
        plt.plot(x, s * multiplier, color=color, marker="o", label=label_name)

    if list_dates_vertical_lines:
        # plot vertical lines
        for str_date in list_dates_vertical_lines:
            # Define the datetime value where you want to add the vertical line
            vertical_line_time = pd.to_datetime(str_date)
            # Add a vertical line at the specified x value
            plt.axvline(x=vertical_line_time, color="black", linestyle="--")
        # also get the first line as the start of the campain
        # assume we set the start and end of campaign at equal times
        # we want to calculate the nubmer of impresions and clicks and uplift from before to fter
        datetime_campaign_start = list_dates_vertical_lines[0]
        df_before = df[df.index < datetime_campaign_start]
        df_after = df[df.index >= datetime_campaign_start]
        # impressions
        num_impressions_before = df_before["impressions"].mean()
        num_impressions_after = df_after["impressions"].mean()
        uplift_impressions = round(
            (num_impressions_after / num_impressions_before - 1) * 100, 0
        )
        title += f", uplift impressions = {uplift_impressions}%"
        # clicks
        num_clicks_before = df_before["clicks"].mean()
        num_clicks_after = df_after["clicks"].mean()
        uplift_clicks = round((num_clicks_after / num_clicks_before - 1) * 100, 0)
        title += f", uplift clicks = {uplift_clicks}%"

    # Add horizontal lines
    if list_horizontal_lines:
        for y_value in list_horizontal_lines:
            ax.hlines(
                y=y_value,
                xmin=x.min(),
                xmax=x.max(),
                colors="black",
                linestyles="dashdot",
            )

    # Add horizontal lines _2
    # solid, dashed, dotted, dashdot
    if list_horizontal_lines_2:
        for y_value in list_horizontal_lines_2:
            ax.hlines(
                y=y_value,
                xmin=x.min(),
                xmax=x.max(),
                colors="darkgray",
                linestyles="dashed",
            )

    plt.ylim(ylim)
    plt.title(title, fontsize=25)
    plt.legend(loc="upper left", fontsize=25)

    # Show the plot
    # plt.show()

    if output_file_name:
        if do_printout:
            print(f"Saving plot to {output_file_name}")
        fig.savefig(output_file_name, bbox_inches="tight")

    plt.close()

    return fig


def create_bar_chart(
    df: pd.DataFrame,
    category_column: str,
    value_column: str,
    title: str,
    output_file_name: Optional[str] = None,
) -> plt.Figure:
    """
    Create a bar chart comparing categories with their corresponding values.

    Args:
    df (pd.DataFrame): The input DataFrame.
    category_column (str): The name of the column containing categories.
    value_column (str): The name of the column containing values to plot.
    title (str): The title of the plot.
    output_file_name (Optional[str]): If provided, save the plot to this file.

    Returns:
    plt.Figure: The matplotlib Figure object.
    """
    # Set the style for the plot
    sns.set_style("whitegrid")

    # Create the figure and axis objects
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create the bar plot
    sns.barplot(data=df, x=category_column, y=value_column, ax=ax)

    # Set the title and labels
    ax.set_title(title, fontsize=20)
    ax.set_xlabel(category_column, fontsize=16)
    ax.set_ylabel(value_column, fontsize=16)

    # Increase tick label size
    ax.tick_params(axis="both", which="major", labelsize=14)

    # Rotate x-axis labels if they are long
    plt.xticks(rotation=45, ha="right")

    # Add value labels on top of each bar
    for i in ax.containers:
        ax.bar_label(i, fmt="%.2f", padding=3, fontsize=12)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot if output_file_name is provided
    if output_file_name:
        plt.savefig(output_file_name, dpi=300, bbox_inches="tight")

    return fig


def generate_rainbow_colors(num_colors: int = 12) -> List[Tuple[float, float, float]]:
    """Generate a list of rainbow colors."""
    # Define the colors of the rainbow
    rainbow_colors = [
        (1.0, 0.0, 0.0),  # Red
        (1.0, 0.5, 0.0),  # Orange
        (1.0, 1.0, 0.0),  # Yellow
        (0.0, 1.0, 0.0),  # Green
        (0.0, 0.0, 1.0),  # Blue
        (0.5, 0.0, 1.0),  # Indigo
        (0.5, 0.0, 0.5),  # Violet
    ]

    # reverse
    # rainbow_colors = rainbow_colors[::-1]

    # # Interpolate to get the desired number of colors
    # colors = []
    # for i in range(num_colors):
    #     ratio = i / (num_colors - 1)
    #     index = int(ratio * (len(rainbow_colors) - 1))
    #     next_index = min(index + 1, len(rainbow_colors) - 1)
    #     color = tuple(
    #         rainbow_colors[index][j] * (1 - ratio % 1)
    #         + rainbow_colors[next_index][j] * (ratio % 1)
    #         for j in range(3)
    #     )
    #     colors.append(color)

    # Calculate the number of segments between each color
    num_segments = len(rainbow_colors) - 1
    colors_per_segment = num_colors // num_segments
    remainder = num_colors % num_segments

    # Interpolate to get the desired number of colors
    colors = []
    for i in range(num_segments):
        start_color = np.array(rainbow_colors[i])
        end_color = np.array(rainbow_colors[i + 1])
        for j in range(colors_per_segment + (1 if i < remainder else 0)):
            ratio = j / (colors_per_segment + (1 if i < remainder else 0))
            color = start_color * (1 - ratio) + end_color * ratio
            colors.append(tuple(color))

    return colors
