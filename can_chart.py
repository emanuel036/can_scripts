import os
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MinuteLocator
import numpy as np

# Settings
start_time = ""
end_time = ""
x_axys_interval = 5
can_data = {'speed': True,
            'rpm': False,
            'collision': True,
            'brake_pedal': False,
            'long_acc': False,
            'cruise_control': False}

# Input directory
input_directory = os.path.join(os.path.dirname(__file__), 'data')

# Regex patterns
patterns = {
    'speed': re.compile(r'FEF100#.{2}(.{4})'),
    'rpm': re.compile(r'F00400#.{6}(.{4})'),
    'collision': re.compile(r'F02F.{2}#.{1}(.{1})'),
    'brake_pedal': re.compile(r'FEF127#.{6}(.{1})'),
    'long_acc': re.compile(r'F009.{2}#.{14}(.{2})'),
    'cruise_control': re.compile(r'FEF100#.{7}(.{1})')
}
timestamp_pattern = re.compile(r'\((\d+\.\d+)\)')

# Invert the order of bytes in a hexadecimal string
def invert_bytes(hex_str):
    byte_array = bytearray.fromhex(hex_str)
    byte_array.reverse()
    return byte_array.hex()

# Process the hexadecimal value based on the key
def process_hex_value(key, hex_value):
    if key in ['speed', 'rpm']:
        hex_value = invert_bytes(hex_value)
        
    decimal_value = int(hex_value, 16)
    if key == 'speed':
        return decimal_value * 0.00390625
    elif key == 'rpm':
        return decimal_value * 0.125
    elif key == 'brake_pedal':
        return decimal_value & 0x3
    elif key == 'long_acc':
        return decimal_value * 0.1 - 12.5
    elif key == 'collision':
        return decimal_value
    elif key == 'cruise_control':
        return decimal_value & 0x3
    return decimal_value

# Convert start_time and end_time to datetime objects once
start_time_dt = datetime.strptime(start_time, "%H:%M").time() if start_time else None
end_time_dt = datetime.strptime(end_time, "%H:%M").time() if end_time else None

# Process a single line of input data
def process_line(line, data):
    timestamp_match = timestamp_pattern.search(line)
    if not timestamp_match:
        return

    dt = datetime.fromtimestamp(
        float(timestamp_match.group(1))) - timedelta(hours=3)
    if (start_time_dt and dt.time() < start_time_dt) or \
       (end_time_dt and dt.time() > end_time_dt):
        return

    for key, pattern in patterns.items():
        if can_data[key] and (match := pattern.search(line)):
            data[key][0].append(dt)
            data[key][1].append(process_hex_value(key, match.group(1)))

# Split data into segments based on gaps in time
def split_data(times, values, max_gap_seconds=10):
    segments, gaps, current_segment = [], [], [[], []]
    for i in range(len(times)):
        if i > 0 and (times[i] - times[i-1]).total_seconds() > max_gap_seconds:
            segments.append(
                (np.array(current_segment[0]), np.array(current_segment[1])))
            gaps.append((times[i-1], times[i]))
            current_segment = [[], []]
        current_segment[0].append(times[i])
        current_segment[1].append(values[i])
    if current_segment[0]:
        segments.append(
            (np.array(current_segment[0]), np.array(current_segment[1])))
    return segments, gaps

# Get the title for the graph based on the key
def get_graph_title(key):
    titles = {
        'speed': 'Truck speed',
        'rpm': 'Engine speed',
        'collision': 'CM system status',
        'brake_pedal': 'Brake pedal',
        'long_acc': 'Longitudinal acceleration',
        'cruise_control': 'Cruise control state'
    }
    return titles.get(key, '')

# Set the y-axis ticks and labels based on the key
def set_y_ticks(ax, key):
    if key == 'collision':
        y_ticks = [1, 3, 5, 6, 7, 8, 14]
        y_labels = ['Unavailable', 'Available', 'FCW',
                    'Haptic', 'FCM', 'Limited', 'Error']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
    elif key == 'brake_pedal':
        y_ticks = [0, 1, 2]
        y_labels = ['Not pressed', 'Pressed', 'Error']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
    elif key == 'cruise_control':
        y_ticks = [0, 1, 2]
        y_labels = ['Off', 'On', 'Error']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)

# Plot the chart with the given segments
def plot_chart(segments):
    fig, axes = plt.subplots(sum(can_data.values()), 1, figsize=(10, 15))
    graph_titles = {
        'speed': 'Km/h',
        'rpm': 'RPM',
        'collision': 'Status',
        'brake_pedal': 'Status',
        'long_acc': 'M/s²',
        'cruise_control': 'Status'
    }

    ax_idx = 0
    for key, show in can_data.items():
        if show:
            ax = axes[ax_idx] if isinstance(axes, (list, np.ndarray)) else axes
            ax.set_title(get_graph_title(key))
            ax.set_ylabel(graph_titles[key])
            ax.grid(True)
            for segment in segments[key][0]:
                ax.plot(segment[0], segment[1], label=key)
            for gap in segments[key][1]:
                ax.axvspan(gap[0], gap[1], color='red', alpha=0.3)
            ax.xaxis.set_major_locator(MinuteLocator(interval=x_axys_interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.tick_params(axis='x')
            set_y_ticks(ax, key)
            ax_idx += 1

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3)
    plt.show()

# Process a single input file
def process_file(input_file_path):
    print(f"Parsing file: {os.path.basename(input_file_path)}")
    data = {key: ([], []) for key in patterns if can_data[key]}

    with open(input_file_path, 'r') as file:
        for line in file:
            process_line(line, data)

    for key in data:
        data[key] = (np.array(data[key][0]), np.array(data[key][1]))

    segments = {key: split_data(*data[key]) for key in data}
    plot_chart(segments)


# Check if there are any files to process
files_processed = False

for root, dirs, files in os.walk(input_directory):
    for file in files:
        if file.endswith('.txt'):
            input_file_path = os.path.join(root, file)
            process_file(input_file_path)
            files_processed = True

if not files_processed:
    print("No files to analyze in the directory.")