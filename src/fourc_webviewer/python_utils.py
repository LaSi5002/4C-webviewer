"""Module for python utils."""


def flatten_list(input_list):
    """Flattens a given (multi-level) list into a single list.

    Args:
        input_list (list): list to be flattened.

    Returns:
        list: flattened list.
    """

    output_list = []

    for input_list_item in input_list:
        if isinstance(input_list_item, list):
            output_list.extend(flatten_list(input_list_item))
        else:
            output_list.append(input_list_item)

    return output_list


def find_value_recursively(input_dict, target_key):
    """Finds the value for a specified key within a nested dict recursively.
    Helpful when going through the sections of the input fourc yaml file.

    Args:
        input_dict (dict): input dict to be scanned for the target key
        target_key (string): target key to search for

    Returns:
        any | None: value of the specific target key
    """
    if isinstance(input_dict, dict):
        for key, value in input_dict.items():
            if key == target_key:
                return value
            result = find_value_recursively(value, target_key)
            if result is not None:
                return result
    elif isinstance(input_dict, list):
        for item in input_dict:
            result = find_value_recursively(item, target_key)
            if result is not None:
                return result
    return None


def smart_string2number_cast(input_string):
    """Casts an input_string to float / int if possible. Helpful when dealing
    with automatic to-string conversions from vuetify.VTextField input
    elements.

    Args:
        input_string (str): input string to be converted.
    Returns:
        int | float | str | object: converted value.
    """
    # otherwise boolean values are converted to 0/1
    if not isinstance(input_string, str):
        return input_string
    try:
        # first convert to float
        input_float = float(input_string)
        if input_float.is_integer():
            return int(input_float)
        return input_float
    except (ValueError, TypeError):
        return input_string  # if conversion fails: return original string


def convert_string2number(input_element):
    """Recursively converts strings to int/float where possible in nested lists
    or dictionaries.

    Args:
        input_element (str | list | dict): Input to be converted.

    Returns:
        int | float | str | list | dict: Converted structure with numeric strings cast.
    """
    if isinstance(input_element, list):
        return [convert_string2number(el) for el in input_element]
    elif isinstance(input_element, dict):
        return {k: convert_string2number(v) for k, v in input_element.items()}
    else:
        return smart_string2number_cast(input_element)
