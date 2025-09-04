# script.py
"""Support functions for phosphate hill data processing"""
import re
from enum import IntEnum, unique

# pylint: disable=consider-using-f-string


@unique
class SensorType(IntEnum):
    """Enumerated sensor type."""
    TEROS12 = 1
    SUCTION = 2
    OXYGEN = 3
    LIGHT = 4
    RAIN = 5
    WIND = 6
    TEMPERATURE = 7
    HUMIDITY = 8


@unique
class DataType(IntEnum):
    """Enumerated sensor data type."""
    ADC = 1
    TEMPERATURE = 2
    HUMIDITY_REL = 3
    LIGHT_IR = 4
    LIGHT_UV = 5
    LIGHT_VIS = 6
    EC = 7
    DEGREE_OF_SAT = 8
    WIND_DIRECTION = 9
    WIND_SPEED = 10
    SUCTION = 11
    RAIN_CUM = 12
    RAIN_PERIOD = 13
    PARTIAL_PRESSURE = 14
    PERCENT = 15
    PRESSURE = 16


class SensorInfo:
    """Class object to group sensor parsed info."""

    def __init__(self, id_: int, type_: SensorType, data_type_: str):
        self.id = id_
        self.type = type_
        self.data_type = data_type_

    def __repr__(self):
        return repr("SensorInfo({}, {}, {})".format(self.id, self.type, self.data_type))


class CoefDetail:
    """Interpolation coefficient parameters."""

    def __init__(self, value: float = 1e-18, preview: bool = False):
        self.value = value
        self.preview = preview


DEVICE_ID_LIST = {
    "phosphatehill-1": "33cc6cc0-010a-11ee-ae7d-c5c03c83f7dc",
    "phosphatehill-2": "3a896e50-010a-11ee-ae7d-c5c03c83f7dc",
    "phosphatehill-3": "3f9a94a0-010a-11ee-ae7d-c5c03c83f7dc",
    "phosphatehill-4": "44ec4660-010a-11ee-ae7d-c5c03c83f7dc",
    "rain-wind": "525afee0-010a-11ee-ae7d-c5c03c83f7dc"
}
"""Dictionary of device id's for phosphate hill project."""

class SensorMapInfo:
    """Sensor key info"""
    depth: float
    """Depth installed sensor in metre."""
    layer: str
    """Material layer description."""

    def get_desc(self):
        return f"{self.depth}m [{self.layer}]"

MOS_ID_DEPTH_LOWER = {
    1: 2.2,
    2: 1,
    3: 0.6,
    4: 0.05
}
"""Lower hill, Moisture sensor ID, installation depth below surface."""

MOS_ID_DEPTH_UPPER = {
    5: 2.2,
    6: 1,
    7: 0.6,
    8: 0.05
}
"""Upper hill, Moisture sensor ID, installation depth below surface."""

SUCTION_ID_DEPTH_LOWER = {
    1: 2.2,
    9: 1.6,
    2: 1,
    3: 0.6,
    10: 0.4,
    4: 0.05
}
"""Lower hill, Suction sensor ID, installation depth below surface."""

SUCTION_ID_DEPTH_UPPER = {
    5: 2.2,
    11: 1.6,
    6: 1,
    7: 0.6,
    12: 0.4,
    8: 0.05
}
"""Upper hill, Suction sensor ID, installation depth below surface."""

OXYGEN_ID_DEPTH_LOWER = {
    1: 2.2,
    2: 0.6
}
"""Lower hill, Oxygen sensor ID, installation depth below surface."""

OXYGEN_ID_DEPTH_UPPER = {
    3: 2.2,
    4: 0.6
}
"""Upper hill, Oxygen sensor ID, installation depth below surface."""


def remove_unwanted_keys(keys, device_name_):
    # type: (list[str], str) -> None
    """Removes device_name from list of keys if warranted."""
    unwanted_keys_from_all = (
        "battery_voltage",
        "humidity_internal",
        "temp_internal"
    )
    device_specific_keys = {
        "phosphatehill-3": (
            "suct9",  # Sensor reporting incorrect values
        ),
    }
    for unwanted_key in unwanted_keys_from_all:
        if unwanted_key in keys:
            keys.remove(unwanted_key)

    if device_name_ in device_specific_keys:
        for unwanted_key in device_specific_keys[device_name_]:
            keys.remove(unwanted_key)


def parse_sensorinfo_from_keyname(key_name):
    # type: (str) -> SensorInfo
    """"Parse sensor type from key name."""
    # match = re.match(r"^(mos|suct|oxy|light)[^a-zA-Z]*(\d*)_?(\w*)$", key_name)
    match = re.match(
        r"^(mos|suct|oxy|light|temp|humidity|wind|rain)(\d*)_?(\w*)$", key_name)
    if match is None:
        return None

    meas_type = match.group(3)
    if meas_type == "":
        meas_type = None

    if match.group(1) == "mos":
        sensor_type = SensorType.TEROS12
    elif match.group(1) == "suct":
        sensor_type = SensorType.SUCTION
    elif match.group(1) == "oxy":
        sensor_type = SensorType.OXYGEN
    elif match.group(1) == "light":
        sensor_type = SensorType.LIGHT
    elif match.group(1) == "temp":
        sensor_type = SensorType.TEMPERATURE
    elif match.group(1) == "humidity":
        sensor_type = SensorType.HUMIDITY
    elif match.group(1) == "wind":
        sensor_type = SensorType.WIND
    elif match.group(1) == "rain":
        sensor_type = SensorType.RAIN
    else:
        sensor_type = None

    if match.group(2):
        _id = int(match.group(2))
    else:
        _id = None

    return SensorInfo(_id, sensor_type, meas_type)


def get_data_type(sensor_: SensorInfo, raw: bool = True) -> DataType:
    if not sensor_:
        return None

    _data_type = None
    if sensor_.type == SensorType.TEROS12:
        if sensor_.data_type == "ec":
            _data_type = DataType.EC
        elif sensor_.data_type == "temp":
            _data_type = DataType.TEMPERATURE
        else:
            _data_type = DataType.ADC if raw else DataType.DEGREE_OF_SAT
    elif sensor_.type == SensorType.LIGHT:
        if sensor_.data_type == "ir":
            _data_type = DataType.ADC if raw else DataType.LIGHT_IR
        elif sensor_.data_type == "uv":
            _data_type = DataType.LIGHT_UV
        elif sensor_.data_type == "visible":
            _data_type = DataType.ADC if raw else DataType.LIGHT_VIS
    elif sensor_.type == SensorType.SUCTION:
        _data_type = DataType.TEMPERATURE if raw else DataType.SUCTION
    elif sensor_.type == SensorType.WIND:
        if sensor_.data_type == "dir":
            _data_type = DataType.WIND_DIRECTION
        elif sensor_.data_type == "speed":
            _data_type = DataType.WIND_SPEED
    # elif sensor_.type == SensorType.TEMPERATURE and \
    #         sensor_.data_type in ("ambient"):
    elif sensor_.type == SensorType.TEMPERATURE:
        _data_type = DataType.TEMPERATURE
    elif sensor_.type == SensorType.HUMIDITY and \
            sensor_.data_type in ("ambient"):
        _data_type = DataType.HUMIDITY_REL
    elif sensor_.type == SensorType.RAIN:
        _data_type = DataType.RAIN_PERIOD
    elif sensor_.type == SensorType.OXYGEN:
        if sensor_.data_type == "baro":
            _data_type = DataType.PRESSURE
        elif sensor_.data_type == "percent":
            _data_type = DataType.PERCENT
        elif sensor_.data_type == "temp":
            _data_type = DataType.TEMPERATURE
        else:
            _data_type = DataType.PARTIAL_PRESSURE
    else:
        _data_type = sensor_.data_type
    return _data_type


def get_data_type_from_keyname(key_name: str, raw: bool = True) -> DataType:
    sensor_ = parse_sensorinfo_from_keyname(key_name)
    return get_data_type(sensor_=sensor_, raw=raw)


def get_interp_coef(name_, key_name):
    _coef = CoefDetail()

    # Device specific coefficient map
    coef_map = {
        "phosphatehill-1": {
            # "humidity_ambient": CoefDetail(1e-18, False),
            # "light_ir": CoefDetail(1e-18, False),
            # "light_uv": CoefDetail(1e-18, False),
            # "light_visible": CoefDetail(1e-18, False),
            # "mos1": CoefDetail(1e-18, False),
            # "mos1_ec": CoefDetail(1e-18, False),
            # "mos1_temp": CoefDetail(1e-18, False),
        },  # phosphatehill-1
        "phosphatehill-2": {
        },  # phosphatehill-2
        "phosphatehill-3": {
        },  # phosphatehill-3
        "phosphatehill-4": {
        },  # phosphatehill-4
        "rain-wind": {
        }  # rain-wind
    }

    # Default coefficient parameters
    try:
        _coef = coef_map[name_][key_name]
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


def get_key_unit_labels(key_: str, engineered_: bool = False) -> str:
    _data_type = get_data_type_from_keyname(key_, raw=not engineered_)
    if not _data_type:
        return ""

    unit = ""
    if _data_type == DataType.ADC:
        unit = "ADC"
    elif _data_type in (DataType.DEGREE_OF_SAT,
                        DataType.HUMIDITY_REL,
                        DataType.PERCENT):
        unit = "%"
    elif _data_type == DataType.EC:
        unit = "uS/cm"
    elif _data_type in (DataType.LIGHT_IR, DataType.LIGHT_VIS):
        unit = "W/m^2"
    elif _data_type == DataType.LIGHT_UV:
        unit = "UV Index" if engineered_ else "UV Index * 100"
    elif _data_type == DataType.RAIN_CUM:
        unit = "mm/day"
    elif _data_type == DataType.RAIN_PERIOD:
        unit = "mm/period"
    elif _data_type == DataType.SUCTION:
        unit = "kPa"
    elif _data_type == DataType.TEMPERATURE:
        unit = "Celsius"
    elif _data_type == DataType.WIND_SPEED:
        unit = "km/hr"
    elif _data_type == DataType.WIND_DIRECTION:
        unit = "Deg, Clockwise"
    elif _data_type in (DataType.PARTIAL_PRESSURE,
                        DataType.PRESSURE):
        unit = "mbar"
    return unit


def get_units_array(values, engineered_: bool = False):
    _values = []
    for name in values:
        unit = get_key_unit_labels(key_=name, engineered_=engineered_)
        if unit:
            _values.append(unit)
        else:
            _values.append("N/A")
    return _values


def get_sensor_depth(sensor_key_name):
    sensor_ = parse_sensorinfo_from_keyname(sensor_key_name)
    depth = None
    if not sensor_:
        pass
    elif sensor_.type == SensorType.TEROS12:
        depth = MOS_ID_DEPTH_LOWER.get(sensor_.id)
        if not depth:
            depth = MOS_ID_DEPTH_UPPER.get(sensor_.id)
    elif sensor_.type == SensorType.SUCTION:
        depth = SUCTION_ID_DEPTH_LOWER.get(sensor_.id)
        if not depth:
            depth = SUCTION_ID_DEPTH_UPPER.get(sensor_.id)
    elif sensor_.type == SensorType.OXYGEN:
        depth = OXYGEN_ID_DEPTH_LOWER.get(sensor_.id)
        if not depth:
            depth = OXYGEN_ID_DEPTH_UPPER.get(sensor_.id)
    return depth


def get_sensor_depth_array(values):
    _values = []
    for name in values:
        depth = get_sensor_depth(name)
        _values.append(depth if depth else "N/A")
    return _values


def get_uphill_downhill_label_array(values):
    labels = []
    LBL_UP = "uphill"  # pylint: disable=invalid-name
    LBL_DOWN = "downhill"  # pylint: disable=invalid-name

    for name in values:
        sensor_ = parse_sensorinfo_from_keyname(name)
        label = "N/A"
        if not sensor_:
            pass
        elif sensor_.type == SensorType.TEROS12:
            if MOS_ID_DEPTH_LOWER.get(sensor_.id):
                label = LBL_DOWN
            elif MOS_ID_DEPTH_UPPER.get(sensor_.id):
                label = LBL_UP
        elif sensor_.type == SensorType.SUCTION:
            if SUCTION_ID_DEPTH_LOWER.get(sensor_.id):
                label = LBL_DOWN
            elif SUCTION_ID_DEPTH_UPPER.get(sensor_.id):
                label = LBL_UP
        elif sensor_.type == SensorType.OXYGEN:
            if OXYGEN_ID_DEPTH_LOWER.get(sensor_.id):
                label = LBL_DOWN
            elif OXYGEN_ID_DEPTH_UPPER.get(sensor_.id):
                label = LBL_UP
        labels.append(label)
    return labels

def get_sensor_label(site: str, key: str):
    depth = get_sensor_depth(key)
    if depth <= 0.05:
        return F"{depth}m [Top Soil]"
    if depth >= 2.2:
        return F"{depth}m [Gypsum]"
    if depth > 0:
        if site == "phosphatehill-1":
            if 0.4 <= depth < 1.6:
                return F"{depth}m [Shale]"
            return F"{depth}m [Slime]"
        if site == "phosphatehill-2":
            return F"{depth}m [Shale]"
        if site == "phosphatehill-3":
            return F"{depth}m [Calcaerous Inca Shale]"
        if site == "phosphatehill-4":
            return F"{depth}m [Silt Stone]"
    return None
