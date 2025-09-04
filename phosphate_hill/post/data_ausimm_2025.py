# script.py
# %%
"""Script to extract data for phosphate hill project to excel file."""
import copy
import os
from datetime import date, datetime, timedelta

import pandas as pd
import postprocess
import pyduino_sensor.post as post_sensor
from thingsboard_api import tb_pandas
import xlsxwriter
from phosphatehill import *  # pylint: disable=wildcard-import


START_TIME = date(year=2023, month=6, day=10)
END_TIME = date(year=2025, month=3, day=31)
# END_TIME = date.today()

if type(START_TIME) == date:  # pylint: disable=unidiomatic-typecheck
    START_TIME = datetime.combine(START_TIME, datetime.min.time())
if type(END_TIME) == date:  # pylint: disable=unidiomatic-typecheck
    END_TIME = datetime.combine(END_TIME, datetime.max.time())


account = tb_pandas.Account("")
account.authenticate(username="",
                     password="")

devices = {}
raw_data = {}
resampled = {}
engineered = {}
# interpolated = {}

# Loop through device list to get device keys and data
for device_name, device_id in DEVICE_ID_LIST.items():
    device = tb_pandas.Device(
        account, name=device_name, device_id=device_id)
    device.get_keys_timeseries()
    devices[device_name] = device
    remove_unwanted_keys(device.keys_ts, device_name_=device_name)
    raw_data[device_name] = tb_pandas.convert_to_dataframe(
        device.get_timeseries(
            startTs=START_TIME,
            endTs=END_TIME,
            limit=200000
        ),
        drop_ts=False
    )


# %%
# Perform resampling
for device_name, df_data in raw_data.items():
    _interpolated = postprocess.Interpolation(
        start_time=START_TIME,
        end_time=END_TIME,
        interval=timedelta(days=1),
        ref_data=df_data)
    for key in df_data.columns:
        if key == "rain":
            _interpolated.df[key] = df_data[key].resample(
                rule="D", level=0).sum().round(1)
        else:
            _interpolated.df[key] = df_data[key].resample(
                rule="D", level=0).mean()
            # sensor = parse_sensorinfo_from_keyname(key)
            # if sensor and sensor.type == SensorType.OXYGEN:
            #     _interpolated.df[key] = df_data[key].resample(
            #             rule="D", level=0).mean()
            # else:
            #     coef = get_interp_coef(device_name, key)
            #     _interpolated.interpolate_smooth(key_name=key,
            #                                  coef=coef.value, preview=coef.preview)
    _interpolated.df.index = _interpolated.df.index.map(datetime.date)
    resampled[device_name] = _interpolated.df

# %%
# Make copy of data for converting to engineered values
# for device_name, df in resampled.items():
#     engineered[device_name] = df.copy(deep=True)

# Loop through device list to perform data interpolation
# for device_name in DEVICE_ID_LIST:
#     # print("Interpolating {}".format(device_name))
#     _interpolated = postprocess.Interpolation(
#         start_time=START_TIME,
#         end_time=END_TIME,
#         interval=timedelta(days=1),
#         ref_data=raw_data[device_name])

#     for key in devices[device_name].keys:
#         sensor = parse_sensorinfo_from_keyname(key)
#         if sensor and sensor.type == SensorType.OXYGEN:
#             continue  # Skip processing Oxygen data
#         if key == "rain":
#             # Get aggregated sum of rain data instead of interpolation
#             # rain_sum = devices[device_name].get_data(
#             #     startTs=START_TIME - timedelta(days=1),
#             #     endTs=END_TIME + timedelta(days=1),
#             #     keys="rain",
#             #     agg="SUM",
#             #     interval=timedelta(days=1)
#             # )
#             # rain_df = tb_pandas.convert_to_dataframe(rain_sum)
#             # Aggregated data from thingsboard data has offset,
#             # Remove offset before joining to existing dataframe table.
#             # rain_df.index = rain_df.index - timedelta(hours=12)
#             rain_df = raw_data["rain-wind"].groupby(
#                 pd.Grouper(level="timestamp", freq='D'))["rain"].sum()
#             _interpolated.df = _interpolated.df.join(rain_df, how="left")
#         else:
#             coef = get_interp_coef(device_name, key)
#             _interpolated.interpolate_smooth(key_name=key,
#                                              coef=coef.value, preview=coef.preview)
#     interpolated[device_name] = _interpolated.df

# Perform conversion of data to engineering values
# Make copy of data for converting to engineered values
# %%
# Make copy of data for converting to engineered values
engineered = copy.deepcopy(resampled)

for device_name, df in engineered.items():
    for column_name, series in df.items():
        sensor_info = parse_sensorinfo_from_keyname(column_name)
        data_type = get_data_type(sensor_info, raw=False)
        if data_type is None:
            continue
        if data_type == DataType.LIGHT_UV:
            df[column_name] = post_sensor.SI114X.calculate_uv_index(
                value=series.values)
        elif data_type == DataType.LIGHT_IR:
            df[column_name] = \
                post_sensor.SI114X.calculate_intensity_from_typical(type_="ir",
                                                                    value=series.values)
        elif data_type == DataType.LIGHT_VIS:
            df[column_name] = \
                post_sensor.SI114X.calculate_intensity_from_typical(type_="vis",
                                                                    value=series.values)
        elif data_type == DataType.DEGREE_OF_SAT:
            df[column_name] = post_sensor.normalise(value=series.values,
                                                    min_=1500,
                                                    max_=3000) * 100
        elif data_type == DataType.SUCTION:
            # pylint: disable=line-too-long
            df[column_name] = post_sensor.SuctionHeatDissipation.delta_temperature_to_kpa(value=series.values,
                                                                                          dry=5.1,
                                                                                          wet=3.7)
            # pylint: enable=line-too-long


# %%
# Calculate average ground temperature

def calculate_av_ground_temp(df): # pylint: disable=redefined-outer-name
    """Calculate average ground temperature, excluding surface"""
    # Exclude surface temperature due to more variability
    keys = ["mos1_temp", "mos2_temp", "mos3_temp",
            # "mos4_temp",
            "mos5_temp", "mos6_temp", "mos7_temp",
            # "mos8_temp"
    ]
    return df.get(keys).mean(axis=1)

for device_name, df in engineered.items():
    if device_name != "rain-wind":
        df["temp_ground_avg"] = calculate_av_ground_temp(df)


# %%
# Add units to dataframe
for device_name, df in engineered.items():
    # Add units to column labels
    # df.columns = pd.MultiIndex.from_arrays(
    #     [df.columns.values, get_units_array(
    #         df.columns.values, engineered=True)],
    #     names=["", "units"])
    tb_pandas.add_multindex_level(df,
                                  keys=get_units_array(df.columns.get_level_values(0),
                                                       engineered_=True),
                                  level=-1,
                                  axis=1,
                                  name="units",
                                  inplace=True)
    # Add cell location data
    tb_pandas.add_multindex_level(df,
                                  keys=get_uphill_downhill_label_array(
                                      df.columns.get_level_values(0)),
                                  level=-1,
                                  axis=1,
                                  name="Uphill/Downhill",
                                  inplace=True)
    # Add installation depth data
    tb_pandas.add_multindex_level(df,
                                  keys=get_sensor_depth_array(
                                      df.columns.get_level_values(0)),
                                  level=-1,
                                  axis=1,
                                  name="depth below surface (m)",
                                  inplace=True)
    tb_pandas.unique_column_headings_only(df)


# %%
# Write resampled engineered data to Excel file
FILENAME = "phosphatehill_data_{}-{}.xlsx".format(START_TIME.strftime("%Y.%m.%d"),
                                                  END_TIME.strftime("%Y.%m.%d"))
FILE_PATH = os.path.join(FILENAME)

def anonymised_station_name(key_: str, anonymise: bool=False):
    """Get anonymised station name"""
    if not anonymise:
        return key_
    return {
        "phosphatehill-1": "Cell 1",
        "phosphatehill-2": "Cell 2",
        "phosphatehill-3": "Cell 3",
        "phosphatehill-4": "Cell 4",
        "phosphatehill-5": "Cell 5"
    }.get(key_)


def anonymised_sensor_label(site: str, key: str):
    depth = get_sensor_depth(key)
    if depth <= 0.05:
        return F"{depth}m [Topsoil]"
    if depth >= 2.2:
        return F"{depth}m [Tailings]"
        # return F"{depth}m [Fine-grained, non-hydraulic]"
    if depth > 0:
        if site == "phosphatehill-1":
            if 0.4 <= depth < 1.6:
                return F"{depth}m [W. Rock]"
            return F"{depth}m [Slime]"
        if site == "phosphatehill-2":
            return F"{depth}m [W. Rock]"
        if site == "phosphatehill-3":
            return F"{depth}m [W. Rock B]"
        if site == "phosphatehill-4":
            return F"{depth}m [W. Rock C]"
    return None


def chart_rainfall_column(workbook_: xlsxwriter.workbook, y2_axis=False, total_cum=False):
    """Chart rainfall

    Args:
        workbook_ (xlsxwriter.workbook): workbook
        y2_axis (bool, optional): Secondary axis. Defaults to False.
        total_cum (bool, optional): Include total accumulation. Default to False. 

    Returns:
        chart: rainfall chart
    """
    rain_col_num = engineered["rain-wind"].columns.get_level_values(
        0).tolist().index("rain") + 1
    chart = workbook_.add_chart({"type": "column"})
    chart.add_series(
        {
            "name": ["rain-wind", 0, rain_col_num],
            "categories": ["rain-wind", 3, 0, engineered["rain-wind"]["rain"].size + 2, 0],
            "values": ["rain-wind", 3, rain_col_num,
                       engineered["rain-wind"]["rain"].size + 2, rain_col_num],
            "y2_axis": 1 if y2_axis else 0,
        }
    )
    if y2_axis:
        chart.set_y2_axis({"name": "Rain (mm/day)"})
    else:
        chart.set_y_axis({"name": "Rain (mm/day)"})
        chart.set_title({'name': 'Rainfall'})
        chart.set_legend({"none": True})

    chart.set_x_axis(
        {
            "date_axis": True,
            "min": START_TIME,
            "num_format": "mmm\nyyyyy",
            'major_unit_type': 'months',
            'major_unit': 2,
        }
    )
    return chart


def chart_ground_avg_temperature(workbook_: xlsxwriter.workbook, df, site_loc_: str, max_row_: int, y2_axis=False):
    """Create ground average temperature chart.

    Args:
        workbook_ (xlsxwriter.workbook): workbook
        site_loc_ (str): sheet name
        max_row_ (int): Number of data rows
        lower (bool, Optional): Plot lower section, else plot upper.

    Returns:
        chart: combined chart of moisture sensor and rain fall data
    """
    key = "temp_ground_avg"
    col_num = df.columns.get_level_values(0).tolist().index(key) + 1
    chart = workbook_.add_chart({'type': 'line'})
    line_property = {}
    if y2_axis:
        line_property["dash_type"] = "dash"
        line_property["color"] = "black"
    chart.add_series(
        {
            "name": "Ground Temperature (Avg)",
            "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
            "values": [site_loc_, 5, col_num, max_row_ + 4, col_num],
            "y2_axis": 1 if y2_axis else 0,
            "line": line_property
        }
    )

    if y2_axis:
        chart.set_y2_axis({
            "name": "Temperature (\u2103)",
            "min": 0,
        })
    else:
        chart.set_title({"name": F"{anonymised_station_name(key_=site_loc_, anonymise=True)} - Average Ground Temperature"})
        chart.set_y_axis({
            "name": "Temperature (\u2103)",
            "min": 0,
        })
        chart.set_legend({"none": True})
        
    chart.set_x_axis({
        "date_axis": True,
        "min": START_TIME,
        "num_format": "mmm\nyyyyy",
    })
    return chart

# pylint: disable-next=redefined-outer-name
def chart_moisture_sensor(workbook_: xlsxwriter.workbook, df, site_loc_: str, max_row_: int, lower: bool = True):
    """Create combined chart for moisture sensor.

    Args:
        workbook_ (xlsxwriter.workbook): workbook
        site_loc_ (str): sheet name
        max_row_ (int): Number of data rows
        lower (bool, Optional): Plot lower section, else plot upper.

    Returns:
        chart: combined chart of moisture sensor and rain fall data
    """
    chart = workbook_.add_chart({'type': 'line'})
    # pylint: disable-next=redefined-outer-name
    for key in ("mos1", "mos2", "mos3", "mos4") if lower else ("mos5", "mos6", "mos7", "mos8"):
        try:
            col_num = df.columns.get_level_values(0).tolist().index(key) + 1
        except KeyError:
            print(F"Failed Charting {site_loc_}: {key}")
            continue
        else:
            chart.add_series(
                {
                    "name": anonymised_sensor_label(site=site_loc_, key=key),
                    "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                    "values": [site_loc_, 5, col_num, max_row_ + 4, col_num],
                }
            )

    chart.combine(chart_rainfall_column(workbook_=workbook_, y2_axis=True))

    chart.set_y_axis(
        {
            # "name": "Moisture Level (Digital)",
            "name": "Degree of Saturation (%)",
            'max': 70,
            "min": 20,
        }
    )
    chart.set_x_axis(
        {
            "date_axis": True,
            "min": START_TIME,
            "num_format": "mmm\nyyyyy",
            'major_unit_type': 'months',
            'major_unit': 2,
        }
    )

    location = "Downslope" if lower else "Upslope"
    chart.set_legend({"position": "bottom"})
    chart.set_title({"name": F"Moisture Reading ({anonymised_station_name(key_=site_loc_, anonymise=True)} - {location})"})
    return chart


def chart_suction_sensor(workbook_: xlsxwriter.workbook, df, site_loc_: str, max_row_: int, lower: bool = True, y2:str = "rain"):
    """Create combined chart for suction sensor.

    Args:
        workbook_ (xlsxwriter.workbook): workbook
        site_loc_ (str): sheet name
        max_row_ (int): Number of data rows
        lower (bool, Optional): Plot lower section, else plot upper.

    Returns:
        chart: combined chart of moisture sensor and rain fall data
    """
    chart = workbook_.add_chart({'type': 'line'})
    # pylint: disable-next=redefined-outer-name
    if lower:
        keys = ("suct1", "suct9", "suct2", "suct3", "suct10", "suct4")
    else:
        keys = ("suct5", "suct11", "suct6", "suct7", "suct12", "suct8")
    delete_series = []
    for idx, key in enumerate(keys):
        try:
            col_num = df.columns.get_level_values(0).tolist().index(key) + 1
        except (KeyError, ValueError):
            print(F"Failed Charting {site_loc_}: {key}")
            chart.add_series(
                {
                    "name": anonymised_sensor_label(site=site_loc_, key=key),
                    "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                    "values": "{1}",
                }
            )
            delete_series.append(idx+1)
        else:
            chart.add_series(
                {
                    "name": anonymised_sensor_label(site=site_loc_, key=key),
                    "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                    "values": [site_loc_, 5, col_num, max_row_ + 4, col_num],
                }
            )

    if y2 == "temp":
        chart.combine(chart_ground_avg_temperature(
            workbook_=workbook, df=df, site_loc_=site_loc_, max_row_=max_row_, y2_axis=True))
    else:
        chart.combine(chart_rainfall_column(workbook_=workbook_, y2_axis=True))

    chart.set_y_axis(
        {
            "name": "Log\u2081\u2080(Suction) (kPa)",
            "log_base": 10,
            "num_format": "0E+00",
            "min": 1e0,
        }
    )
    chart.set_x_axis(
        {
            "date_axis": True,
            "min": START_TIME,
            "num_format": "mmm\nyyyyy",
        }
    )

    location = "Downhill" if lower else "Uphill"
    chart.set_legend({"position": "bottom",
                      "delete_series": delete_series})
    chart.set_title({"name": F"{anonymised_station_name(key_=site_loc_, anonymise=True)} ({location}) - Suction Reading"})
    return chart


def chart_bulk_ec(workbook_: xlsxwriter.workbook, df, site_loc_: str, max_row_: int, lower: bool = True):
    """Create combined chart for bulk EC.

    Args:
        workbook_ (xlsxwriter.workbook): workbook
        site_loc_ (str): sheet name
        max_row_ (int): Number of data rows
        lower (bool, Optional): Plot lower section, else plot upper.

    Returns:
        chart: combined chart of moisture sensor and rain fall data
    """
    chart = workbook_.add_chart({'type': 'line'})
    # pylint: disable-next=redefined-outer-name
    if lower:
        keys = ("mos1_ec", "mos2_ec", "mos3_ec", "mos4_ec")
    else:
        keys = ("mos5_ec", "mos6_ec", "mos7_ec", "mos8_ec")
    delete_series = []
    for idx, key in enumerate(keys):
        try:
            col_num = df.columns.get_level_values(0).tolist().index(key) + 1
        except (KeyError, ValueError):
            print(F"Failed Charting {site_loc_}: {key}")
            chart.add_series({
                "name": anonymised_sensor_label(site=site_loc_, key=key),
                "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                "values": "{1}",
            })
            delete_series.append(idx+1)
        else:
            chart.add_series({
                "name": anonymised_sensor_label(site=site_loc_, key=key),
                "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                "values": [site_loc_, 5, col_num, max_row_ + 4, col_num],
            })

    chart.combine(chart_rainfall_column(workbook_=workbook_, y2_axis=True))

    # chart.set_y_axis({
    #     "name": "EC (uS/cm)",
    #     "min": 0,
    #     "max": 500,
    #     "major_unit": 50,
    # })
    chart.set_y_axis({
        "name": "Log\u2081\u2080(EC) (uS/cm)",
        "log_base": 10,
        "num_format": "0E+00",
        "min": 1e0,
        "max": 1e4,
    })
    chart.set_x_axis({
        "date_axis": True,
        "min": START_TIME,
        "num_format": "mmm\nyyyyy",
    })

    location = "Downhill" if lower else "Uphill"
    chart.set_legend({"position": "bottom",
                      "delete_series": delete_series})
    chart.set_title({"name": F"{anonymised_station_name(key_=site_loc_, anonymise=True)} ({location}) - Bulk Electrical Conductivity"})
    return chart


def chart_oxygen_percent(workbook_: xlsxwriter.workbook, df, site_loc_: str, max_row_: int, lower: bool = True):
    """Create combined chart for gaseus oxygen percentage.

    Args:
        workbook_ (xlsxwriter.workbook): workbook
        site_loc_ (str): sheet name
        max_row_ (int): Number of data rows
        lower (bool, Optional): Plot lower section, else plot upper.

    Returns:
        chart: combined chart of moisture sensor and rain fall data
    """
    chart = workbook_.add_chart({'type': 'line'})
    # pylint: disable-next=redefined-outer-name
    if lower:
        keys = ("oxy1_percent", "oxy2_percent")
    else:
        keys = ("oxy3_percent", "oxy4_percent")
    delete_series = []
    for idx, key in enumerate(keys):
        try:
            col_num = df.columns.get_level_values(0).tolist().index(key) + 1
        except (KeyError, ValueError):
            print(F"Failed Charting {site_loc_}: {key}")
            chart.add_series(
                {
                    "name": anonymised_sensor_label(site=site_loc_, key=key),
                    "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                    "values": "{1}",
                }
            )
            delete_series.append(idx+1)
        else:
            chart.add_series(
                {
                    "name": anonymised_sensor_label(site=site_loc_, key=key),
                    "categories": [site_loc_, 5, 0, max_row_ + 4, 0],
                    "values": [site_loc_, 5, col_num, max_row_ + 4, col_num],
                }
            )

    chart.combine(chart_rainfall_column(workbook_=workbook_, y2_axis=True))

    chart.set_y_axis(
        {
            "name": "Gas Oxygen (%)",
            "min": 0,
        }
    )
    chart.set_x_axis(
        {
            "date_axis": True,
            "min": START_TIME,
            "num_format": "mmm\nyyyyy",
        }
    )

    location = "Downhill" if lower else "Uphill"
    chart.set_legend({"position": "bottom",
                      "delete_series": delete_series})
    chart.set_title({"name": F"{anonymised_station_name(key_=site_loc_, anonymise=True)} ({location}) - Gaseous Oxygen"})
    return chart


with pd.ExcelWriter(FILE_PATH, engine="xlsxwriter",
                    # date_format="dd/mm/yyyy",
                    # datetime_format="dd/mm/yyyy HH:MM:SS",
                    ) as excel_file:
    workbook = excel_file.book
    for device_name, df in engineered.items():
        df.to_excel(excel_file, sheet_name=device_name,
                    columns=df.columns.values)

        worksheet = excel_file.sheets[device_name]
        # Get the dimensions of the dataframe.
        (max_row, max_col) = df.shape

        if device_name == "rain-wind":
            worksheet.insert_chart(1, 3, chart_rainfall_column(workbook_=workbook,
                                                               total_cum=False))
        else:
            worksheet.insert_chart(1, 2, chart_moisture_sensor(workbook_=workbook,
                                                               df=df,
                                                               site_loc_=device_name,
                                                               max_row_=max_row,
                                                               lower=True))
            worksheet.insert_chart(1, 10, chart_moisture_sensor(workbook_=workbook,
                                                                df=df,
                                                                site_loc_=device_name,
                                                                max_row_=max_row,
                                                                lower=False))
            worksheet.insert_chart(16, 2, chart_bulk_ec(workbook_=workbook,
                                                        df=df,
                                                        site_loc_=device_name,
                                                        max_row_=max_row,
                                                        lower=True))
            worksheet.insert_chart(16, 10, chart_bulk_ec(workbook_=workbook,
                                                         df=df,
                                                         site_loc_=device_name,
                                                         max_row_=max_row,
                                                         lower=False))
            worksheet.insert_chart(31, 2, chart_suction_sensor(workbook_=workbook,
                                                               df=df,
                                                               site_loc_=device_name,
                                                               max_row_=max_row,
                                                               lower=True))
            worksheet.insert_chart(31, 10, chart_suction_sensor(workbook_=workbook,
                                                                df=df,
                                                                site_loc_=device_name,
                                                                max_row_=max_row,
                                                                lower=False))
            worksheet.insert_chart(46, 2, chart_oxygen_percent(workbook_=workbook,
                                                               df=df,
                                                               site_loc_=device_name,
                                                               max_row_=max_row,
                                                               lower=True))
            worksheet.insert_chart(46, 10, chart_oxygen_percent(workbook_=workbook,
                                                                df=df,
                                                                site_loc_=device_name,
                                                                max_row_=max_row,
                                                                lower=False))
            worksheet.insert_chart(61, 2, chart_ground_avg_temperature(workbook_=workbook,
                                                                       df=df,
                                                                       site_loc_=device_name,
                                                                       max_row_=max_row,
                                                                       y2_axis=False
                                                                       ))
            worksheet.insert_chart(61, 10, chart_suction_sensor(workbook_=workbook,
                                                               df=df,
                                                               site_loc_=device_name,
                                                               max_row_=max_row,
                                                               lower=True,
                                                               y2="temp"))
            worksheet.insert_chart(61, 18, chart_suction_sensor(workbook_=workbook,
                                                                df=df,
                                                                site_loc_=device_name,
                                                                max_row_=max_row,
                                                                lower=False,
                                                                y2="temp"))
