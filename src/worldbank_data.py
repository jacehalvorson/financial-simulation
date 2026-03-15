"""World Bank data loading and processing."""

import pandas as pd
from pathlib import Path


def load_worldbank_stock_data(data_file='static/API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv'):
    """
    Load World Bank S&P Global Equity Indices data.

    Returns:
        DataFrame with countries as rows and years as columns
    """
    # Load the CSV (skip metadata rows)
    df = pd.read_csv(data_file, skiprows=4)

    # Set country name as index
    df = df.set_index('Country Name')

    # Get only year columns (1960-2024)
    year_cols = [str(year) for year in range(1960, 2025)]
    year_cols = [col for col in year_cols if col in df.columns]

    return df[year_cols]


def get_country_stock_returns(country_name, years=20, data_file='static/API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv'):
    """
    Get stock market returns for a specific country.

    Args:
        country_name: Name of the country
        years: Number of years of historical data (from most recent)
        data_file: Path to World Bank CSV file

    Returns:
        dict with 'dates' and 'values' lists (compounded starting at 1)
    """
    df = load_worldbank_stock_data(data_file)

    if country_name not in df.index:
        raise ValueError(f"Country '{country_name}' not found in dataset")

    # Get the country's data
    country_data = df.loc[country_name]

    # Convert to numeric, replacing empty strings with NaN
    country_data = pd.to_numeric(country_data, errors='coerce')

    # Get the last N years with data
    country_data = country_data.dropna()

    if len(country_data) == 0:
        raise ValueError(f"No data available for {country_name}")

    # Take last N years
    country_data = country_data.tail(years)

    # Convert index to integers (years)
    years_list = [int(year) for year in country_data.index]
    returns = country_data.values.tolist()

    # Calculate compounded values starting at 1
    compounded_values = [1.0]
    for return_pct in returns:
        compounded_values.append(compounded_values[-1] * (1 + return_pct / 100))

    # Round values
    compounded_values = [round(v, 4) for v in compounded_values]

    return {
        'dates': [years_list[0] - 1] + years_list,
        'values': compounded_values
    }


def get_available_countries(data_file='static/API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv'):
    """
    Get list of countries that have stock market data.

    Returns:
        List of country names that have at least some data
    """
    df = load_worldbank_stock_data(data_file)

    # Find countries with at least some data
    countries_with_data = []
    for country in df.index:
        country_data = pd.to_numeric(df.loc[country], errors='coerce')
        if country_data.notna().any():
            countries_with_data.append(country)

    return sorted(countries_with_data)


# Default countries to display (major markets)
DEFAULT_COUNTRIES = [
    'United States',
    'China',
    'United Kingdom',
    'Germany',
    'Japan',
    'Canada',
    'France',
    'India',
    'Australia',
    'Brazil',
]
