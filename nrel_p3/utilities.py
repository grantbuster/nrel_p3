"""
Interface with pricing tool csv export
"""

import re
import pandas as pd
from warnings import warn


def employee_id_regex(text):
    """Get the employee id from this format: "name, name (eid)"

    Returns
    -------
    out : str | None
    """
    pattern = r'\((\d+)\)(?!.*\(\d+\))'
    match = re.search(pattern, str(text))
    if match:
        return match.group(1)
    else:
        return None


def filter(data, filters):
    """Run a filter to subselect rows from the table.

    Parameters
    ----------
    data : pd.DataFrame
        Data table to filter.
    filters : dict
        Set of filters where keys are columns in the estimate file and
        values are one or more items to sub select in the column.

    Returns
    -------
    subdf : pd.DataFrame
        Subset of the planning table based on requested filters
    """
    mask = True
    for key, value in filters.items():
        if value is not None:
            if isinstance(value, (str, int, float)):
                imask = data[key] == value
            elif isinstance(value, (list, tuple)):
                imask = data[key].isin(value)
            mask &= imask
            if not any(imask):
                warn(f'Filter {key}=={value} resulted in zero results')

    if isinstance(mask, pd.Series):
        return data[mask].copy()
    else:
        return data.copy()
