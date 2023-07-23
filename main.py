import os

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import HourLocator, DateFormatter
from matplotlib.ticker import MultipleLocator


class SensorTrafficData:
    def __init__(self, sensor_id, place, all_day, hourly_data):
        self.sensor_id = sensor_id
        self.place = place
        self.all_day = all_day
        self.hourly_data = hourly_data


class NO2Measurement:
    def __init__(self, timestamp, value):
        self.timestamp = pd.to_datetime(timestamp)
        self.value_ug_by_m3 = int(value)
        self.value_ppb = self.convert_to_ppb()

    def convert_to_ppb(self):
        # Constants
        molarMassNO2 = 46.0055  # g/mol
        pressureAir = 1013  # hPa
        idealGasConstant = 8.3144  # J/(K*mol) = (m^3*Pa)/(K*mol)
        temperatureAir = 300  # K

        # Compute molar concentrations
        molarConcentrationAir = (pressureAir * 100) / (idealGasConstant * temperatureAir)
        molarConcentrationNO2 = (self.value_ug_by_m3 * 1e-6) / molarMassNO2

        # Compute mixing ratio in ppb
        return (molarConcentrationNO2 / molarConcentrationAir) * 1e9
        #return self.value_ug_by_m3 / 46.0055


def read_traffic_csv_to_data_model(csv_file):
    data_models = []
    df = pd.read_csv(csv_file)
    for index, row in df.iterrows():
        sensor_id = row["Sensor ID"]
        place = row["Place"]
        all_day = row["ALL DAY"]
        hourly_data = {
            0: row["00:00"],
            1: row["01:00"],
            2: row["02:00"],
            3: row["03:00"],
            4: row["04:00"],
            5: row["05:00"],
            6: row["06:00"],
            7: row["07:00"],
            8: row["08:00"],
            9: row["09:00"],
            10: row["10:00"],
            11: row["11:00"],
            12: row["12:00"],
            13: row["13:00"],
            14: row["14:00"],
            15: row["15:00"],
            16: row["16:00"],
            17: row["17:00"],
            18: row["18:00"],
            19: row["19:00"],
            20: row["20:00"],
            21: row["21:00"],
            22: row["22:00"],
            23: row["23:00"]
        }
        data_model = SensorTrafficData(sensor_id, place, all_day, hourly_data)
        data_models.append(data_model)
    return data_models


def read_no2_csv_file(file_path):
    measurements = []
    data = pd.read_csv(file_path, header=None)
    for _, row in data.iterrows():
        row_entries_array = row[0].split(';')
        measurement = NO2Measurement(row_entries_array[0] + ' ' + row_entries_array[1], row_entries_array[2])
        measurements.append(measurement)
    return measurements


def plot_measurements(csv_files, traffic_data):
    fig, ax1 = plt.subplots(figsize=(15, 8))

    ax2 = ax1.twinx()

    timestamps = []

    for file in csv_files:
        measurements = read_no2_csv_file(file)
        file_name = os.path.splitext(os.path.basename(file))[0]

        ax1.plot([m.timestamp for m in measurements], [m.convert_to_ppb() for m in measurements], label=f"{file_name} (NO2)")

        for measurement in measurements:
            if measurement.timestamp not in timestamps:
                timestamps.append(measurement.timestamp)

    for traffic_station in traffic_data:
        ax2.plot(timestamps,
                 [traffic_station.hourly_data[timestamp.hour] for timestamp in timestamps],
                 linestyle='--',
                 label=traffic_station.place + ' Traffic')


    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('NO2 Measurement in ppb')
    ax2.set_ylabel('Traffic Data')

    plt.title('NO2 Measurements with Traffic Information and Traffic Data in Munich')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')

    ax1.xaxis.set_major_locator(HourLocator(interval=1))
    ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M'))
    ax1.yaxis.set_major_locator(MultipleLocator(base=2))

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    traffic_csv_file = "data/traffic.csv"
    sensor_traffic_data_models = read_traffic_csv_to_data_model(traffic_csv_file)

    no2_csv_files = ["data/stachus.csv", "data/lothstrasse.csv", "data/landshuter_allee.csv",
                     "data/johanneskirchen.csv", "data/allach.csv"]
    plot_measurements(no2_csv_files, sensor_traffic_data_models)

    for sensor_data in sensor_traffic_data_models:
        print(f"Sensor ID: {sensor_data.sensor_id}")
        print(f"Place: {sensor_data.place}")
        print(f"ALL DAY: {sensor_data.all_day}")
        print()

