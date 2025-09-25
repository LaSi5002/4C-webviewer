"""Input file visualization."""

import copy
import re
from pathlib import Path

import lnmmeshio
import numexpr as ne
import numpy as np
import plotly.express as px
from fourc_webviewer.input_file_utils.io_utils import (
    get_variable_data_by_name_in_funct_item,
)


# functional expressions / constants known by 4C, that are replaced by the numpy counterpart during evaluation
DEF_FUNCT = ["exp", "sqrt", "log", "sin", "cos", "tan", "heaviside", "pi"]


def get_variable_names_in_funct_expression(funct_expression: str):
    """Returns all variable names present in a functional expression, using regular expressions."""
    vars_found = re.findall(r"[A-Za-z_]+", funct_expression)
    return [
        v for v in vars_found if v not in DEF_FUNCT and v not in ["t", "x", "y", "z"]
    ]


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
    if (
        "COMPONENT"
        in state_data.funct_section[state_data.selected_funct][
            state_data.selected_funct_item
        ]
    ):
        function_copy = copy.deepcopy(
            state_data.funct_section[state_data.selected_funct][
                state_data.selected_funct_item
            ]["SYMBOLIC_FUNCTION_OF_SPACE_TIME"]
        )
    elif (
        "VARIABLE"
        in state_data.funct_section[state_data.selected_funct][
            state_data.selected_funct_item
        ]
    ):
        function_copy = construct_funct_string_from_variable_data(
            variable_name=state_data.funct_section[state_data.selected_funct][
                state_data.selected_funct_item
            ]["NAME"],
            funct_section_item=state_data.funct_section[state_data.selected_funct],
        )
    if not function_copy:
        function_copy = "0.0"

    # construct function strings for the variables to replace them into
    # the function later on
    variable_funct_strings = {
        k: construct_funct_string_from_variable_data(
            variable_name=k,
            funct_section_item=state_data.funct_section[state_data.selected_funct],
        )
        for k in get_variable_names_in_funct_expression(funct_expression=function_copy)
    }

    num_of_time_points = 1000  # number of discrete time points used for plotting
    data = {
        "t": np.linspace(0, state_data.funct_plot["max_time"], num_of_time_points),
        "f(t)": return_function_from_funct_string(
            funct_string=function_copy, variable_funct_strings=variable_funct_strings
        )(
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


def return_function_from_funct_string(funct_string: str, variable_funct_strings: dict):
    """Create function from funct string.

    Args:
        funct_string (str): Funct definition
        variable_funct_strings (dict): Funct definitions of the variables
            involved in funct_string to be replaced in the expression

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
        # funct_string copy
        funct_string_copy = funct_string

        # replace variables by their functional expressions
        for k, v in variable_funct_strings.items():
            funct_string_copy = re.sub(
                rf"(?<![A-Za-z]){k}(?![A-Za-z])", v, funct_string_copy
            )

        # replace the defined functions in the funct_string with "<DEF_FUNCT>"
        for i in range(len(DEF_FUNCT)):
            funct_string_copy = funct_string_copy.replace(
                DEF_FUNCT[i], f"np.{DEF_FUNCT[i]}"
            )

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


def construct_funct_string_from_variable_data(
    variable_name: str, funct_section_item: dict
):
    """Constructs a functional string from the given data for a function variable."""

    # retrieve variable data
    variable_data = get_variable_data_by_name_in_funct_item(
        variable_name=variable_name, funct_section_item=funct_section_item
    )

    # construct functional expression string for supported types
    funct_string = ""
    match variable_data["TYPE"]:
        case "linearinterpolation":
            # get times and values
            times, values = np.array(variable_data["TIMES"]), np.array(
                variable_data["VALUES"]
            )

            # consistency check: time should start with 0.0
            if float(times[0]) != 0.0:
                raise Exception("Time should start with 0 in the TIMES section")
            # loop through time instants and the functional expressions,
            # using heaviside functions to differentiate between time intervals
            funct_string = "("
            for time_instant_index, time_instant in enumerate(times[:-1]):
                if time_instant_index != 0:
                    funct_string += "+"

                funct_string += f"({values[time_instant_index]}+({values[time_instant_index+1]}-{values[time_instant_index]})/({times[time_instant_index+1]}-{time_instant})*(t-{time_instant}))*heaviside(t-{time_instant})*heaviside({times[time_instant_index+1]}-t)"

            funct_string += ")"

        case "multifunction":
            # get times and values
            times, descriptions = (
                np.array(variable_data["TIMES"]),
                variable_data["DESCRIPTION"],
            )

            # consistency check: time should start with 0.0
            if float(times[0]) != 0.0:
                raise Exception("Time should start with 0 in the TIMES section")
            # loop through time instants and the functional expressions,
            # using heaviside functions to differentiate between time intervals
            funct_string = "("
            for time_instant_index, time_instant in enumerate(times[:-1]):
                if time_instant_index != 0:
                    funct_string += "+"

                funct_string += f"({descriptions[time_instant_index]}*heaviside(t-{time_instant})*heaviside({times[time_instant_index+1]}-t))"

            funct_string += ")"

        case _:
            # warning that this variable type is not yet supported for visualization
            print(f"Variable with {variable_data} not supported for visualization!")

    return funct_string
