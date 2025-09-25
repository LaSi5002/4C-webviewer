"""Input file visualization."""

import copy
import re
from pathlib import Path

import lnmmeshio
import numexpr as ne
import numpy as np
import plotly.express as px


def function_plot_figure(state_data):
    """Get function plot figure.

    Args:
        state_data (trame_server.core.Server): Trame server state

    Returns:
        plotly.graph_objects._figure.Figure: Figure to be plotted
    """

    # check whether any of the values within the function plot settings
    # is None type (can happen temporarily while changing the values): then write 0 instead
    # of it for the figure plot
    for item_key, item_val in state_data.funct_plot.items():
        if item_val != 0.0 and not item_val:
            state_data.funct_plot[item_key] = 0.0

    # check if the function is None type (can happen temporarily while
    # changing the values): then write 0 instead of it for the figure
    # plot
    function_copy = copy.deepcopy(
        state_data.funct_section[state_data.selected_funct][
            state_data.selected_funct_item
        ]["SYMBOLIC_FUNCTION_OF_SPACE_TIME"]
    )
    if not function_copy:
        function_copy = "0.0"

    num_of_time_points = 1000  # number of discrete time points used for plotting
    data = {
        "t": np.linspace(0, state_data.funct_plot["max_time"], num_of_time_points),
        "f(t)": return_function_from_funct_string(function_copy)(
            np.full((num_of_time_points,), state_data.funct_plot["x_val"]),
            np.full((num_of_time_points,), state_data.funct_plot["y_val"]),
            np.full((num_of_time_points,), state_data.funct_plot["z_val"]),
            np.linspace(0, state_data.funct_plot["max_time"], num_of_time_points),
        ),
    }

    # create figure object with the given data
    fig = px.line(
        data,
        x="t",
        y="f(t)",
        title=f"{state_data.selected_funct}: {state_data.selected_funct_item}",
    )

    # update layout of the figure
    fig.update_layout(
        title=dict(
            font=dict(size=20, family="Arial", color="black"),
            x=0.5,  # center the title
        ),
        xaxis=dict(
            title="t",
            tickfont=dict(size=16, family="Arial", color="black"),
            tickformat=".2f",
            showline=True,
            linewidth=2,
            linecolor="black",
            mirror=True,
        ),
        yaxis=dict(
            title="f(t)",
            tickfont=dict(size=16, family="Arial", color="black"),
            tickformat=".2f",
            showline=True,
            linewidth=2,
            linecolor="black",
            mirror=True,
        ),
        font=dict(family="Arial", size=20, color="black"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig


def return_function_from_funct_string(funct_string):
    """Create function from funct string.

    Args:
        funct_string (str): Funct definition

    Returns:
        callable: callable function of x, y, z, t
    """

    def funct_using_eval(x, y, z, t):
        """Evaluate function expression for given positional x, y, z
        coordinates and time t values.

        Args:
            x (double): x-coordinate
            y (double): y-coordinate
            z (double): z-coordinate
            t (double): time t

        Returns:
            parsed object using ast.literal_eval
        """
        # defined functions to be replaced: <def_funct> becomes <np.funct>
        def_funct = ["exp", "sqrt", "log", "sin", "cos", "tan", "heaviside"]

        # funct_string copy
        funct_string_copy = funct_string

        # replace the defined functions in the funct_string with "<def_funct>"
        for i in range(len(def_funct)):
            funct_string_copy = funct_string_copy.replace(
                def_funct[i], f"np.{def_funct[i]}"
            )

        # replace pi as well
        funct_string_copy = funct_string_copy.replace("pi", "np.pi")

        # replace the used power sign
        funct_string_copy = funct_string_copy.replace("^", "**")

        # replace variables
        funct_string_copy = (
            funct_string_copy.replace("x", str(x))
            .replace("y", str(y))
            .replace("z", str(z))
            .replace("t", str(t))
        )

        # for heaviside: np.heaviside takes two arguments -> second argument denotes the function value at the first argument -> we set it by default to 0
        funct_string_copy = re.sub(
            r"heaviside\((.*?)\)", r"heaviside(\1,0)", funct_string_copy
        )  # usage of raw strings, (.*?) is a non greedy capturing, and \1 replaces the captured value

        return eval(
            funct_string_copy, {"np": np}, {}
        )  # this parses string in as a function

    return np.frompyfunc(funct_using_eval, 4, 1)
