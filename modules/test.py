"""
Tests
"""

import datetime
from zoneinfo import ZoneInfo

import meteostat as met
import pandas as pd
from geopy import distance
from wetterdienst import Settings as dwd_settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest as dwd

dwd_stations = (
    dwd(
        parameter="temperature_air",
        resolution="hourly",
    )
    .all()
    .df
)

weatherstations_max_distance = 100

dwd_hourly_parameters = dwd.discover(flatten=False)["hourly"]
dwd_keys_lvl_1 = list(dwd_hourly_parameters.keys())
dwd_keys_lvl_2 = list(
    set(
        sum(
            [list(dwd_hourly_parameters[key].keys()) for key in dwd_keys_lvl_1],
            [],
        )
    )
)
dwd_parameter_units = {}
for key1 in dwd_keys_lvl_1:
    for key2 in dwd_keys_lvl_2:
        if dwd_hourly_parameters[key1].get(key2) != None:
            dwd_parameter_units[key2] = dwd_hourly_parameters[key1][key2]["origin"]

dwd_categories = {
    "temperature_air": "Lufttemperatur",
    "cloud_type": "Bewölkungstyp",
    "cloudiness": "Bewölkungsgrad",
    "dew_point": "Taupunkt",
    "wind_extreme": "Extremer Wind",
    "moisture": "Feuchtigkeit",
    "precipitation": "Niederschlag",
    "pressure": "Druck",
    "temperature_soil": "Temperatur Erdreich",
    "solar": "Solarstrahlung",
    "sun": "Sonne",
    "visibility": "Sicht",
    "weather_phenomena": "Wetterphänomene",
    "wind": "Wind",
    "wind_synoptic": "Wind synoptisch",
}

dwd_parameters = {
    "radiation_sky_long_wave": {"tit": "atmosphärische Gengenstrahlung"},
    "humidity_absolute": {"tit": "absolute Feuchte"},
    "temperature_soil_mean_010": {"tit": "Erdbodentemperatur in 10 cm Tiefe"},
    "temperature_air_mean_200": {"tit": "Lufttemperatur in 2 m Höhe"},
    "precipitation_height": {"tit": "Niederschlagshöhe"},
    "precipitation_indicator": {"tit": "Niederschlagsindikator"},
    "cloud_type_layer4": {"tit": "Wolkenart der 4. Schicht"},
    "cloud_type_layer1": {"tit": "Wolkenart der 1. Schicht"},
    "weather_text": {"tit": "Wetterbeschreibung"},
    "cloud_type_layer3": {"tit": "Wolkenart der 3. Schicht"},
    "quality": {"tit": "Qualität"},
    "wind_gust_max": {"tit": "stärktste Windböe"},
    "sun_zenith_angle": {"tit": "Zenitwinkel der Sonne"},
    "temperature_dew_point_mean_200": {"tit": "Taupunkttemperatur in 2 m Höhe"},
    "temperature_soil_mean_002": {"tit": "Erdbodentemperatur in 2 cm Tiefe"},
    "cloud_cover_total_indicator": {"tit": "Gesamtbedeckungsgrad Index"},
    "humidity": {"tit": "relative Feuchte"},
    "cloud_cover_layer4": {"tit": "Bedeckungsgrad der 4. Schicht"},
    "sunshine_duration": {"tit": "Sonnenscheindauer"},
    "cloud_height_layer4": {"tit": "Wolkenhöhe der 4. Schicht"},
    "temperature_soil_mean_050": {"tit": "Erdbodentemperatur in 50 cm Tiefe"},
    "cloud_height_layer1": {"tit": "Wolkenhöhe der 1. Schicht"},
    "true_local_time": {"tit": "Ortszeit"},
    "pressure_air_sea_level": {"tit": "Luftdruck auf Meereshöhe"},
    "pressure_vapor": {"tit": "Dampfdruck"},
    "cloud_type_layer2": {"tit": "Wolkenart der 2. Schicht"},
    "radiation_global": {"tit": "Globalstrahlung"},
    "temperature_wet_mean_200": {"tit": "Feuchtetemperatur"},
    "wind_speed": {"tit": "Windgeschwindigkeit"},
    "visibility_range": {"tit": "Sichtweite"},
    "visibility_range_indicator": {"tit": "Sichtweite Index"},
    "cloud_height_layer2": {"tit": "Wolkenhöhe der 2. Schicht"},
    "pressure_air_site": {"tit": "Luftdruck auf Stationshöhe"},
    "temperature_soil_mean_005": {"tit": "Erdbodentemperatur in 5 cm Tiefe"},
    "radiation_sky_short_wave_diffuse": {"tit": "diffuse Strahlung"},
    "cloud_cover_layer3": {"tit": "Bedeckungsgrad der 3. Schicht"},
    "cloud_cover_layer2": {"tit": "Bedeckungsgrad der 2. Schicht"},
    "end_of_interval": {"tit": "Intervallende"},
    "weather": {"tit": "Wetter"},
    "wind_direction": {"tit": "Windrichtung"},
    "temperature_soil_mean_020": {"tit": "Erdbodentemperatur in 20 cm Tiefe"},
    "cloud_height_layer3": {"tit": "Wolkenhöhe der 3. Schicht"},
    "precipitation_form": {"tit": "Niederschlagsart"},
    "cloud_cover_layer1": {"tit": "Bedeckungsgrad der 1. Schicht"},
    "cloud_cover_total": {"tit": "Gesamtbedeckungsgrad"},
    "temperature_soil_mean_100": {"tit": "Erdbodentemperatur in 100 cm Tiefe"},
}

# Parameter, die nicht in den interpolierten Daten auftauchen, aber über DWD-Stationen abrufbar sind
additional_parameters = {
    "radiation_global": {"tit": "Globalstrahlung"},
    "radiation_sky_short_wave_diffuse": {"tit": "diffuse Strahlung"},
    "radiation_sky_long_wave": {"tit": "atmosphärische Gengenstrahlung"},
    "humidity_absolute": {"tit": "absolute Feuchte"},
    "temperature_wet_mean_200": {"tit": "Feuchtetemperatur"},
    "pressure_air_site": {"tit": "Luftdruck auf Stationshöhe"},
    "pressure_vapor": {"tit": "Dampfdruck"},
    "precipitation_indicator": {"tit": "Niederschlagsindikator"},
    "precipitation_form": {"tit": "Niederschlagsart"},
    "temperature_soil_mean_002": {"tit": "Erdbodentemperatur in 2 cm Tiefe"},
    "temperature_soil_mean_005": {"tit": "Erdbodentemperatur in 5 cm Tiefe"},
    "temperature_soil_mean_010": {"tit": "Erdbodentemperatur in 10 cm Tiefe"},
    "temperature_soil_mean_020": {"tit": "Erdbodentemperatur in 20 cm Tiefe"},
    "temperature_soil_mean_050": {"tit": "Erdbodentemperatur in 50 cm Tiefe"},
    "temperature_soil_mean_100": {"tit": "Erdbodentemperatur in 100 cm Tiefe"},
    "cloud_cover_total_indicator": {"tit": "Gesamtbedeckungsgrad Index"},
    "cloud_cover_total": {"tit": "Gesamtbedeckungsgrad"},
    "cloud_cover_layer1": {"tit": "Bedeckungsgrad der 1. Schicht"},
    "cloud_cover_layer2": {"tit": "Bedeckungsgrad der 2. Schicht"},
    "cloud_cover_layer3": {"tit": "Bedeckungsgrad der 3. Schicht"},
    "cloud_cover_layer4": {"tit": "Bedeckungsgrad der 4. Schicht"},
    "cloud_type_layer1": {"tit": "Wolkenart der 1. Schicht"},
    "cloud_type_layer2": {"tit": "Wolkenart der 2. Schicht"},
    "cloud_type_layer3": {"tit": "Wolkenart der 3. Schicht"},
    "cloud_type_layer4": {"tit": "Wolkenart der 4. Schicht"},
    "cloud_height_layer1": {"tit": "Wolkenhöhe der 1. Schicht"},
    "cloud_height_layer2": {"tit": "Wolkenhöhe der 2. Schicht"},
    "cloud_height_layer3": {"tit": "Wolkenhöhe der 3. Schicht"},
    "cloud_height_layer4": {"tit": "Wolkenhöhe der 4. Schicht"},
    "visibility_range": {"tit": "Sichtweite"},
    "visibility_range_indicator": {"tit": "Sichtweite Index"},
    "sun_zenith_angle": {"tit": "Zenitwinkel der Sonne"},
    "temperature_air_mean_200": {"tit": "Lufttemperatur in 2 m Höhe"},
    "temperature_dew_point_mean_200": {"tit": "Taupunkttemperatur in 2 m Höhe"},
    "wind_gust_max": {"tit": "stärktste Windböe"},
    "humidity": {"tit": "relative Feuchte"},
    "precipitation_height": {"tit": "Niederschlagshöhe"},
}

for par in dwd_parameters:
    dwd_parameters[par]["cat_en"] = [
        key
        for key in dwd_hourly_parameters
        if par in list(dwd_hourly_parameters[key].keys())
    ][0]
    dwd_parameters[par]["cat_de"] = dwd_categories[dwd_parameters[par]["cat_en"]]
    dwd_parameters[par]["unit"] = dwd_parameter_units[par]
    dwd_parameters[par]["num_format"] = f'#,##0.0" {dwd_parameters[par]["unit"]}"'

meteo_codes = {
    "TEMP": {
        "orig_name": "Air Temperature",
        "tit": "Temperatur",
        "unit": "°C",
        "num_format": '#,##0.0" °C"',
        "dwd_param_de": "Lufttemperatur in 2 m Höhe",
        "dwd_param_en": "temperature_air_mean_200",
    },
    "TAVG": {
        "orig_name": "Average Temperature",
        "tit": "Durchschnittstemperatur",
        "unit": "°C",
        "num_format": '#,##0.0" °C"',
        "dwd_param_de": None,
        "dwd_param_en": None,
    },
    "TMIN": {
        "orig_name": "Minimum Temperature",
        "tit": "Minimaltemperatur",
        "unit": "°C",
        "num_format": '#,##0.0" °C"',
        "dwd_param_de": None,
        "dwd_param_en": None,
    },
    "TMAX": {
        "orig_name": "Maximum Temperature",
        "tit": "Maximaltemperatur",
        "unit": "°C",
        "num_format": '#,##0.0" °C"',
        "dwd_param_de": None,
        "dwd_param_en": None,
    },
    "DWPT": {
        "orig_name": "Dew Point",
        "tit": "Taupunkt",
        "unit": "°C",
        "num_format": '#,##0.0" °C"',
        "dwd_param_de": "Taupunkttemperatur in 2 m Höhe",
        "dwd_param_en": "temperature_dew_point_mean_200",
    },
    "PRCP": {
        "orig_name": "Total Precipitation",
        "tit": "Niederschlag",
        "unit": "mm",
        "num_format": '#,##0.0" mm"',
        "dwd_param_de": "Niederschlagshöhe",
        "dwd_param_en": "precipitation_height",
    },
    "WDIR": {
        "orig_name": "Wind (From) Direction",
        "tit": "Windrichtung",
        "unit": "°",
        "num_format": '#,##0.0"°"',
        "dwd_param_de": "Windrichtung",
        "dwd_param_en": "wind_direction",
    },
    "WSPD": {
        "orig_name": "Average Wind Speed",
        "tit": "Windgeschwindigkeit",
        "unit": "km/h",
        "num_format": '#,##0.0" km/h"',
        "dwd_param_de": "Windgeschwindigkeit",
        "dwd_param_en": "wind_speed",
    },
    "WPGT": {
        "orig_name": "Wind Peak Gust",
        "tit": "max. Windböe",
        "unit": "km/h",
        "num_format": '#,##0" km/h"',
        "dwd_param_de": "stärktste Windböe",
        "dwd_param_en": "wind_gust_max",
    },
    "RHUM": {
        "orig_name": "Relative Humidity",
        "tit": "rel. Luftfeuchtigkeit",
        "unit": "%",
        "num_format": '#,##0"%"',
        "dwd_param_de": "relative Feuchte",
        "dwd_param_en": "humidity",
    },
    "PRES": {
        "orig_name": "Sea-Level Air Pressure",
        "tit": "Luftdruck (Meereshöhe)",
        "unit": "hPa",
        "num_format": '#,##0.0" hPa"',
        "dwd_param_de": "Luftdruck auf Meereshöhe",
        "dwd_param_en": "pressure_air_sea_level",
    },
    "SNOW": {
        "orig_name": "Snow Depth",
        "tit": "Schneehöhe",
        "unit": "m",
        "num_format": '#,##0" mm"',
        "dwd_param_de": None,
        "dwd_param_en": None,
    },
    "TSUN": {
        "orig_name": "Total Sunshine Duration",
        "tit": "Sonnenstunden",
        "unit": "min",
        "num_format": '#,##0" min"',
        "dwd_param_de": "Sonnenscheindauer",
        "dwd_param_en": "sunshine_duration",
    },
    "COCO": {
        "orig_name": "Weather Condition Code",
        "tit": "Wetterlage",
        "unit": "",
        "num_format": "0",
        "dwd_param_de": None,
        "dwd_param_en": None,
    },
}


all_params = dwd_parameters
all_params.update(meteo_codes)

lat = 50
lon = 8

ms_parameter = ["Globalstrahlung"]

dwd_settings.si_units = False

all_pars_en = list(dwd_parameters.keys())

if ms_parameter != []:
    add_pars_en = [
        [key for key in dwd_parameters if dwd_parameters[key].get("tit") == par_de][0]
        for par_de in ms_parameter
    ]
else:
    add_pars_en = ["temperature_air_mean_200"]


start = datetime.datetime(2020, 1, 1, 0, 0, tzinfo=ZoneInfo("Europe/Berlin"))
end = datetime.datetime(2020, 12, 31, 23, 59, tzinfo=ZoneInfo("Europe/Berlin"))
if end.year == datetime.datetime.now().year:
    end = datetime.datetime.now()

# alle dwd-Stationen (alle, die Temperatur in stündlicher Auflösung haben)
request = dwd(
    parameter=["temperature_air_mean_200"],
    resolution="hourly",
    start_date=start,
    end_date=end,
)
# ...mit Abstandsspalte
dwd_all_stations = request.filter_by_distance(
    latitude=lat,
    longitude=lon,
    distance=1_000_000,
).df

# dwd-Stationen, die Daten für den gewünschten Zeitraum haben
dwd_all_stations = dwd_all_stations[dwd_all_stations["from_date"] <= start]
dwd_all_stations = dwd_all_stations[dwd_all_stations["to_date"] >= end]


# verfügbare Wetterstationen von meteostat
# in x Meter entfernung zur gegebenen Addresse
# mit stündlichen Daten in der erforderlichen Zeitperiode
meteostat_stations = (
    met.Stations()
    .nearby(lat, lon, weatherstations_max_distance * 1_000)
    .inventory("hourly", (start.replace(tzinfo=None), end.replace(tzinfo=None)))
).fetch()
meteostat_stations["distance"] = meteostat_stations["distance"] / 1000

# für alle dwd_parameter alle Station-IDs auflisten, die Daten für den Parameter haben
for par in all_pars_en:
    try:
        df = (
            dwd(
                parameter=par,
                resolution="hourly",
                start_date=start,
                end_date=end,
            )
            .all()
            .df
        )
        df = df[df["from_date"] <= start]
        df = df[df["to_date"] >= end]
        dwd_parameters[par]["dwd_station_ids"] = df["station_id"].values
    except:
        pass

dwd_all_stations.reset_index(inplace=True)
# dwd_closest_station = dwd_all_stations.iloc[[0], :]

# closest station per parameter
for par in dwd_parameters:
    dwd_parameters[par]["closest_station"] = None

    if dwd_parameters[par].get("dwd_station_ids") is not None:
        for rank in range(len(dwd_all_stations)):
            if (
                dwd_all_stations.iloc[rank]["station_id"]
                in dwd_parameters[par]["dwd_station_ids"]
            ):
                dwd_parameters[par]["closest_station"] = dwd_all_stations.iloc[rank]
                break

for par in meteo_codes:
    meteo_codes[par]["closest_station"] = None

    for rank in range(len(meteostat_stations)):
        columns = (
            met.Hourly(
                meteostat_stations.index[rank],
                start.replace(tzinfo=None),
                end.replace(tzinfo=None),
            )
            .fetch()
            .dropna(how="all", axis=1)
            .columns
        )
        if par in [col.upper() for col in columns]:
            meteo_codes[par]["closest_station"] = meteostat_stations.iloc[rank]
            break


meteostat_stations["Parameters"] = [
    meteo_codes[col.upper()]["tit"]
    for station_id in meteostat_stations.index
    for col in (
        met.Hourly(station_id, start.replace(tzinfo=None), end.replace(tzinfo=None))
        .normalize()
        .fetch()
        .dropna(how="all", axis=1)
        .columns
    )
]


data = (
    met.Hourly(
        meteostat_stations.index[0],
        start.replace(tzinfo=None),
        end.replace(tzinfo=None),
    )
    .normalize()
    .fetch()
    .dropna(how="all", axis=1)
    .columns
)

# distance test


p1_x = dwd_all_stations.loc[51, "latitude"]
p1_y = dwd_all_stations.loc[51, "longitude"]
p1_t = (p1_x, p1_y)

p2_x = dwd_all_stations.loc[54, "latitude"]
p2_y = dwd_all_stations.loc[54, "longitude"]
p2_t = (p2_x, p2_y)
dist = distance.distance(p1_t, p2_t)
