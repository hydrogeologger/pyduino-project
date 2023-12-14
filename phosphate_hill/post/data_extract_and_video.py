#!/usr/bin/env python3
#%%
# Initial setup and obtain thingsboard account authentication
from dataclasses import dataclass
from enum import IntEnum, unique
from datetime import (datetime, timedelta)
import re
from thingsboard_api import tb_pandas
import postprocess
from postprocess.filehandler import FileCorrelation

START_TIME = datetime(2023, 6, 5)
END_TIME = datetime(2023, 12, 18)

account = tb_pandas.Account("http://monitoring.uqgec.org")
account.authenticate(username="viewonly@ipl.com", password="viewonly")

device_id_list = {
    "phosphatehill-1" : "33cc6cc0-010a-11ee-ae7d-c5c03c83f7dc",
    "phosphatehill-2" : "3a896e50-010a-11ee-ae7d-c5c03c83f7dc",
    "phosphatehill-3" : "3f9a94a0-010a-11ee-ae7d-c5c03c83f7dc",
    "phosphatehill-4" : "44ec4660-010a-11ee-ae7d-c5c03c83f7dc",
    "rain-wind" : "525afee0-010a-11ee-ae7d-c5c03c83f7dc"
}

MOS_ID_DEPTH_LOWER = {
    1: 2.2,
    2: 1,
    3: 0.6,
    4: 0.05
}
MOS_ID_DEPTH_UPPER = {
    5: 2.2,
    6: 1,
    7: 0.6,
    8: 0.05
}
SUCTION_ID_DEPTH_LOWER = {
    1: 2.2,
    9: 1.6,
    2: 1,
    3: 0.6,
    10: 0.4,
    4: 0.05
}
SUCTION_ID_DEPTH_UPPER = {
    5: 2.2,
    11: 1.6,
    6: 1,
    7: 0.6,
    12: 0.4,
    8: 0.05
}
OXYGEN_ID_DEPTH_LOWER = {
    1: 2.2,
    2: 0.6
}
OXYGEN_ID_DEPTH_UPPER = {
    3: 2.2,
    4: 0.6
}

# @dataclass
# class Teros12Info:
#     id: int
#     adc: int
#     temp: float
#     ec: float
#     depth: float

# @dataclass
# class SuctionInfo:
#     id: int
#     delta_t: float
#     depth: float

# @dataclass
# class OxygenSensorInfo:
#     id: int
#     value: float
#     baro: float
#     percent: float
#     temperature: float
#     depth: float

# def get_mos_id(key_name):
#     val = re.match(r"^mos(\d+).*$", key_name)
#     if val is None:
#         return None
#     return int(val.group(1))

# def get_suction_id(key_name):
#     val = re.match(r"^suct(\d+).*$", key_name)
#     if val is None:
#         return None
#     return int(val.group(1))

# def get_oxygen_id(key_name):
#     val = re.match(r"^oxy(\d+).*$", key_name)
#     if val is None:
#         return None
#     return int(val.group(1))

@dataclass
class CoefDetail:
    value: float = 1e-18
    preview: bool = False

@unique
class SensorType(IntEnum):
    TEROS12 = 1
    SUCTION = 2
    OXYGEN = 3
    LIGHT = 4

@dataclass
class SensorInfo:
    id: int
    type: SensorType
    data_type: str

def parse_sensorinfo_from_keyname(key_name):
    match = re.match(r"^(mos|suct|oxy|light)[^a-zA-Z]*(\d*)_?(\w*)$", key_name)
    if match is None:
        return None

    if match.group(1) == "mos":
        sensor_type = SensorType.TEROS12
    elif match.group(1) == "suct":
        sensor_type = SensorType.SUCTION
    elif match.group(1) == "oxy":
        sensor_type = SensorType.OXYGEN
    elif match.group(1) == "light":
        sensor_type = SensorType.LIGHT

    if match.group(2):
        _id = int(match.group(2))
    else:
        _id = None

    meas_type = match.group(3)
    if meas_type == "":
        meas_type = None
    return SensorInfo(_id, sensor_type, meas_type)

@dataclass
class CameraInfo():
    filename: str
    image_dir: str


def get_interp_coef(device_name, key_name):
    _coef = CoefDetail()
    coef_map = {
        "phosphatehill-1": {
            # "humidity_ambient": CoefDetail(1e-18, False),
            # "light_ir": CoefDetail(1e-18, False),
            # "light_uv": CoefDetail(1e-18, False),
            # "light_visible": CoefDetail(1e-18, False),
            # "mos1": CoefDetail(1e-18, False),
            # "mos1_ec": CoefDetail(1e-18, False),
            # "mos1_temp": CoefDetail(1e-18, False),
        }, # phosphatehill-1
        "phosphatehill-2" : {
        }, # phosphatehill-2
        "phosphatehill-3" : {
        }, # phosphatehill-3
        "phosphatehill-4" : {
        }, # phosphatehill-4
        "rain-wind" : {
        } # rain-wind
    }
    try:
        _coef = coef_map[device_name][key_name]
    except KeyError:
        _sensor = parse_sensorinfo_from_keyname(key_name)
        if _sensor is None:
            return _coef
        if _sensor.type == SensorType.SUCTION:
            _coef.value = 1e-19
        elif _sensor.type == SensorType.OXYGEN:
            _coef.value = 1e-20
            if _sensor.data_type is None or _sensor.data_type == "":
                _coef.preview = True
    return _coef

def remove_unwanted_keys(keys, device_name):
    unwanted_keys_from_all = (
            "battery_voltage",
            "humidity_internal",
            "temp_internal"
            )
    device_specific_keys = {
        "phosphatehill-3" : (
                            "suct9", # Sensor reporting incorrect values
                            ),
    }
    for unwanted_key in unwanted_keys_from_all:
        if unwanted_key in keys:
            keys.remove(unwanted_key)

    if device_name in device_specific_keys:
        for unwanted_key in device_specific_keys[device_name]:
            keys.remove(unwanted_key)

def si114x_infrared_to_intensity(adc, gain=14.5, typical=452.38):
    """Converts Silicon Lab SI1145 ADC value to intensity (W/m^2)

    Args:
        adc (int): _description_
        gain (float, optional): _description_. Defaults to 14.5.
        typical (float, optional): _description_. Defaults to 452.38.

    Returns:
        _type_: _description_
    """
    if gain == 0:
        gain = 1
    return adc * gain / typical

def delta_temperature_to_kpa(value, dry=5.1, wet=3.7):
    """Converts a heat dissipation temperature delta to pressure

    Args:
        value (float):
        dry (float, optional): _description_. Defaults to 3.7.
        wet (float, optional): _description_. Defaults to 5.1.

    Returns:
        _type_: _description_
    """
    alpha = (value - wet) / (dry - wet)
    return pow(10, 6 * (1 - alpha) )


#%%
# Loop through device keys and get data from thingsboard

if __name__ == "__main__":
    devices = {}
    data = {}
    interpolated = {}

    # Loop through device list to get device keys and data
    for device_name, device_id in device_id_list.items():
        device = tb_pandas.Device(account, name=device_name, device_id=device_id)
        device.get_keys()
        devices[device_name] = device
        remove_unwanted_keys(device.keys, device_name=device_name)
        data[device_name] = tb_pandas.convert_to_dataframe(
                device.get_data(
                        startTs=START_TIME,
                        endTs=END_TIME,
                        limit=50000
                ),
                drop_ts=False
            )

    #%%
    # Loop through device list to perform data interpolation
    for device_name in device_id_list:
        print(f"Interpolating {device_name}")
        _interpolated = postprocess.Interpolation(
                start_time = START_TIME + timedelta(days=1),
                end_time = END_TIME - timedelta(days=1),
                interval = timedelta(days=1),
                data = data[device_name])

        for key in devices[device_name].keys:
            sensor = parse_sensorinfo_from_keyname(key)
            if sensor and sensor.type == SensorType.OXYGEN:
                continue
            if key == "rain":
                # Get aggregated sum of rain data instead of interpolation
                rain_sum = devices[device_name].get_data(
                        startTs = START_TIME + timedelta(days=1),
                        endTs = END_TIME - timedelta(days=1),
                        keys = "rain",
                        agg = "SUM",
                        interval = timedelta(days=1)
                    )
                rain_df = tb_pandas.convert_to_dataframe(rain_sum)
                # Aggregated data from thingsboard data has offset,
                # Remove offset before joining to existing dataframe table.
                rain_df.index = rain_df.index - timedelta(hours=12)
                _interpolated.df = _interpolated.df.join(rain_df, how="inner")
            else:
                coef = get_interp_coef(device_name, key)
                _interpolated.interpolate_smooth(key_name=key,
                        coef=coef.value, preview=coef.preview)
        interpolated[device_name] = _interpolated.df

    #%%
    # Perform conversion of interpolated data to engineering values
    for device_name in device_id_list:
        print(f"Converting {device_name} engineering values.")
        for column in interpolated[device_name].columns[1:]:
            sensor = parse_sensorinfo_from_keyname(column)
            if sensor is None:
                continue
            if sensor.type == SensorType.LIGHT:
                if sensor.data_type == "ir":
                    interpolated[device_name][column] = si114x_infrared_to_intensity(
                            interpolated[device_name][column].values)
                elif sensor.data_type == "uv":
                    interpolated[device_name][column] = \
                            interpolated[device_name][column].values / 100
                elif sensor.data_type == "visible":
                    interpolated[device_name][column] = si114x_infrared_to_intensity(
                            interpolated[device_name][column].values,
                            typical=8.277)
            elif sensor.type == SensorType.TEROS12:
                if sensor.data_type is None:
                    interpolated[device_name][column] = postprocess.normalise(
                            interpolated[device_name][column].values,
                            low = 1500,
                            high = 3000) * 100
            elif sensor.type == SensorType.SUCTION:
                interpolated[device_name][column] = delta_temperature_to_kpa(
                        interpolated[device_name][column].values
                        )


# %%
# Perform mapped correlation of files
def camera_id_to_strptime_format(id):
    return f"%Y-%m-%d_%H%M_phosphatehill-camera-{id}"

def get_cam_image_folder_from_id(id):
    folder = (
        "cam1_1down",
        "cam2_2down_3down",
        "cam3_3up_4up",
        "cam4_4down",
        "cam5_1up",
        "cam6_2up"
    )
    try:
        return folder[id-1]
    except IndexError:
        return ""

from pandas import (date_range, DatetimeIndex)
map_values = date_range(
    start = START_TIME + timedelta(days=1) + timedelta(hours=12),
    end = END_TIME - timedelta(days=1) + timedelta(hours=12),
    freq = timedelta(days=1)
).tolist()
# map_values.append(datetime(2023, 7, 2)) # Day of rain event
# map_values.append(datetime(2023, 7, 7)) # Max moisture post rain
# map_values.append(END_TIME)
# map_values.sort()

images = {}
for cam_id in range(1, 7):
    images[cam_id] = FileCorrelation(
            format_ = camera_id_to_strptime_format(cam_id),
            path = f"C:\\Users\\uqltan14\\Desktop\\photo_phosphate_hill\\{get_cam_image_folder_from_id(cam_id)}"
    )

    images[cam_id].parse_files()
    images[cam_id].map_to_files_datetime(
            map_values = map_values,
            ref_date_time = map_values,
            data = map_values
            )

# %%
# Perform plotting of figures
# %matplotlib qt
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
from matplotlib.gridspec import GridSpec
from matplotlib.dates import DateFormatter

# params = {'legend.fontsize': 12,
#           'figure.figsize': (10, 5),
#           'axes.labelsize': 16,
#           'axes.titlesize': 16,
#           'axes.axisbelow': True,
#           'xtick.labelsize': 14,
#           'ytick.labelsize': 14,
#           'font.weight':'bold',
#           'font.sans-serif':'Arial',
#           'axes.labelweight':'bold',
#           'lines.linewidth': 2}

# pylab.rcParams.update(params)

mosaic = [
    ["rain",        "ir",  "map_level",  "map_camera"],
    ["mos_down_1",  "mos_up_1",  "cam1", "cam2"],
    ["mos_down_2",  "mos_up_2",  "cam3", "cam4"],
    ["mos_down_3",  "mos_up_3",  "cam5",  "cam6"],
    ["mos_down_4",   "mos_up_4",  "ab",  "ac"],
]

col3 = [['rain'], ['mos_down_1'], ['mos_down_2'], ['mos_down_3'], ['mos_down_4']]
col4 = [['ir'], ['mos_up_1'], ['mos_up_2'], ['mos_up_3'], ['mos_up_4']]
col1 = [['map_level'], ['cam1'], ['cam3'], ['cam5']]
col2 = [['map_camera'], ['cam2'], ['cam4'], ['cam6']]
mosaic = [
    [col1, col2, col3, col4]
]

px = 1/plt.rcParams['figure.dpi']
fig = plt.figure(
        num=1,
        layout="constrained",
        figsize = (1920*px, 1080*px)
        # layout="tight"
)
plt.rcParams['axes.grid'] = True
plt.show(block=False)

ax = fig.subplot_mosaic(
    mosaic=mosaic,
    sharex=True
)

# NROWS = 6
# NCOLS = 4
# ax = {}
# i = 1
# for row in mosaic:
#     for col in row:
#         if col not in ax:
#             if i > 1:
#                 ax[col] = fig.add_subplot(NROWS, NCOLS, i, sharex=ax["rain"])
#             else:
#                 ax[col] = fig.add_subplot(NROWS, NCOLS, i)
#             i+=1

# swap_index(interpolated['rain-wind'])

# Plot Rainfall
ax["rain"].bar(
    interpolated["rain-wind"].index,
    interpolated["rain-wind"].rain,
    label = "rain"
)

# Plot IR
ax["ir"].bar(
    interpolated["phosphatehill-2"].index.values,
    interpolated["phosphatehill-2"].light_ir.values,
    label = device
)
# for device in device_id_list:
#     try:
#         ax["ir"].plot(
#             interpolated[device].index.values,
#             interpolated[device].light_ir.values,
#             label = device
#         )
#     except AttributeError:
#         pass

def get_station_number_from_device_name(name):
    match_val = re.match(r"^phosphatehill-(\d+)$", name)
    if match_val is None:
        return 0
    return int(match_val.group(1))

# Plot MOS
for device in device_id_list:
    station_id = get_station_number_from_device_name(device)
    if station_id <= 0:
        continue
    for sensor_id, depth in MOS_ID_DEPTH_LOWER.items():
        ax[f"mos_down_{station_id}"].plot(
                interpolated[device].index,
                interpolated[device][f"mos{sensor_id}"],
                label = f"{depth} m"
        )
    for sensor_id, depth in MOS_ID_DEPTH_UPPER.items():
        ax[f"mos_up_{station_id}"].plot(
                interpolated[device].index,
                interpolated[device][f"mos{sensor_id}"],
                label = f"{depth} m"
        )



## Handle axis
for axes in ax:
    val_match = re.match(r"^(map|cam).*$", axes)
    # Remove axes for image and maps subplots
    if val_match is not None:
        if val_match.group(1) is not None:
            ax[axes].get_shared_x_axes().remove(ax[axes])
            ax[axes].axis("off")
            # ax[axes].sharex = False
    if axes == "rain":
        ax[axes].set_ylabel(
                "RAINFALL (mm)",
                fontweight='bold'
        )
        ax[axes].grid(axis='x')
    elif axes == "ir":
        ax[axes].set_ylabel(
                "IR INTENSITY\n(W/m^2)",
                fontweight='bold'
        )
        # ax[axes].legend(
        #         loc = "best",
        #         # loc='lower center',
        #         ncol = 2
        # )
    else:
        val_match = re.match(r"^(mos)_(\w+)_(\d?)$", axes)
        if val_match is not None:
            if val_match.group(1) == "mos":
                ax[axes].set_ylim(bottom=20, top=70)
                handles, labels = ax[axes].get_legend_handles_labels()
                ax[axes].legend(
                        reversed(handles),
                        reversed(labels),
                        title = "Depth",
                        loc = "upper right",
                        # bbox_to_anchor=(0.5, 1.05),
                        ncol = 2
                )
                if val_match.group(2) == "up":
                    ax[axes].set_title(
                            f"Cell #{val_match.group(3)} - Uphill",
                            x=0.01,
                            y=0.85,
                            horizontalalignment = "left"
                    )
                else:
                    ax[axes].set_title(
                            f"Cell #{val_match.group(3)} - Downhill",
                            x=0.01,
                            y=0.85,
                            horizontalalignment = "left"
                    )
                    ax[axes].set_ylabel(
                            "DEGREE OF\nSATURATION (%)",
                            fontweight='bold'
                    )
                if val_match.group(3) == "4":
                    ax[axes].set_xlabel(
                            "DATE (month/year)",
                            fontweight='bold'
                    )
                    date_form = DateFormatter("%b/%Y")
                    ax[axes].xaxis.set_major_formatter(date_form)
                    ax[axes].tick_params(axis='x', labelrotation=15)
                    # ax[axes].set_xlim(left=datetime(2023,6, 1))



img = plt.imread("C:\\Users\\uqltan14\\Desktop\\photo_phosphate_hill\\phosphatehill-camera_locations.png")
ax["map_camera"].imshow(img, aspect="equal")

img = plt.imread("C:\\Users\\uqltan14\\Desktop\\photo_phosphate_hill\\cell_layer_info.png")
ax["map_level"].imshow(img, aspect="equal")

from time import sleep
import os
img_artist = {}
avxlines = {}
for image_index, _datetime in enumerate(map_values):
    for axes in ax:
        val_match = re.match(r"^(mos).*$", axes)
        if val_match:
            if image_index == 0:
                avxlines[axes] = ax[axes].axvline(map_values[image_index], color='r')
            else:
                avxlines[axes].set_xdata(map_values[image_index])
    for cam_id in range(1, 7):
        img = plt.imread(images[cam_id].filepaths[image_index])
        if image_index == 0:
            img_artist[cam_id] = ax[f"cam{cam_id}"].imshow(img, aspect="equal")
        else:
            img_artist[cam_id].set_data(img)
        # title = f"Camera #{i} - {images[i].date_times[image_index].strftime('%Y-%m-%d %H:%M')}"
        ax[f"cam{cam_id}"].set_title(
                f"Camera #{cam_id}",
                x = 0.5,
                y = 0.88,
                bbox = {
                    "facecolor" : 'white',
                    "alpha" : 0.5
                }
        )
        # if cam_id == 1:
        #     ax[f"cam{cam_id}"].text(
        #             x = 1300,
        #             y = -200,
        #             s = _datetime.strftime('%Y-%m-%d'),
        #             horizontalalignment = "center",
        #             verticalalignment = "top",
        #             # transform = ax[f"cam{cam_id}"].transAxes
        #     )

        # ax[f"cam{cam_id}"].text(
        #         .5,
        #         .9,
        #         title,
        #         horizontalalignment = 'center',
        #         transform = ax[f"cam{cam_id}"].transAxes
        # )
    fig.suptitle(
        t = _datetime.strftime(f"%d / %b / %Y"),
        fontsize = 20,
        # fontweight = 'bold',
        color = 'r'
    )

    fig.canvas.draw()
    fig.canvas.flush_events()
    output_name = os.getcwd() + '\\photos_for_video' + '\\' + str(image_index).zfill(3) +'.jpg'
    fig.savefig(output_name, format='jpg', dpi=100, bbox_inches='tight', pad_inches=0.1 )
    # print("Pausing...")
    # sleep(2)
print("Finish generating figures")
# %%
# Perform video compilation
import cv2
image_folder = os.getcwd() + '\\photos_for_video'
video_name = 'phosphatehill_' + datetime.now().strftime("%Y-%m-%d") +'.avi'
images_for_video = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
# images.sort(key=lambda x: get_jpg_number(x), reverse=True)
images_for_video.sort(reverse=False)
images_for_video.append(images_for_video[-1])
# images_for_video.append(images_for_video[-1])
frame = cv2.imread(os.path.join(image_folder, images_for_video[0]))
height, width, layers = frame.shape
ratio = 1
width = round(width * ratio)
height = round(height * ratio)
# fourcc = cv2.VideoWriter_fourcc(*'MJPG')
# fourcc = cv2.VideoWriter_fourcc(*'xvid')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter(filename = os.path.join(image_folder, video_name),
                        fourcc = fourcc,
                        fps = 4,
                        frameSize = (width, height))
# video = cv2.VideoWriter(os.path.join(image_folder, video_name), 0, 4, (1920, 1080))

for filename in images_for_video:
    img = cv2.imread(os.path.join(image_folder, filename))
    # img = cv2.resize(img, (1920, 1080))
    # img = cv2.resize(img, (width,height))
    # video.write(cv2.imread(os.path.join(image_folder, filename)))
    video.write(img)

cv2.destroyAllWindows()
video.release()
print("Finish video")
# %%
