import os
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MinuteLocator
import numpy as np

# Input directory
input_directory = os.path.join(os.path.dirname(__file__), 'data')

# Regex to find the desired lines and extract positions 3-6 after the #
patterns = {
    'speed': re.compile(r'FEF100#.{2}(.{4})'),
    'rpm': re.compile(r'F00400#.{6}(.{4})'),
    'collision': re.compile(r'F02F.{2}#.{1}(.{1})')
}
timestamp_pattern = re.compile(r'\((\d+\.\d+)\)')

# Function to invert the order of bytes
def invert_bytes(hex_str):
    return ''.join(reversed([hex_str[i:i+2] for i in range(0, len(hex_str), 2)]))

# Function to process a file and generate the charts
def process_file(input_file_path):
    print(f"Analyzing file: {input_file_path}")

    with open(input_file_path, 'r') as file:
        lines = file.readlines()

    data = {'speed': ([], []), 'rpm': ([], []), 'collision': ([], [])}

    for line in lines:
        timestamp_match = timestamp_pattern.search(line)
        if not timestamp_match:
            continue
        timestamp = float(timestamp_match.group(1))
        dt = datetime.fromtimestamp(timestamp) - timedelta(hours=6)

        for key, pattern in patterns.items():
            match = pattern.search(line)
            if match:
                hex_str = match.group(1)
                inverted_hex_str = invert_bytes(hex_str)
                decimal_value = int(inverted_hex_str, 16)
                if key == 'speed':
                    scaled_value = decimal_value * 0.00390625
                elif key == 'rpm':
                    scaled_value = decimal_value * 0.125
                else:
                    scaled_value = int(match.group(1), 16)
                data[key][0].append(dt)
                data[key][1].append(scaled_value)

    # Convert lists to numpy arrays for better performance in further processing
    for key in data:
        data[key] = (np.array(data[key][0]), np.array(data[key][1]))

    def split_data(times, values, max_gap_seconds=10):
        segments, gaps = [], []
        current_segment_times, current_segment_values = [], []

        for i in range(len(times)):
            if i == 0 or (times[i] - times[i-1]).total_seconds() <= max_gap_seconds:
                current_segment_times.append(times[i])
                current_segment_values.append(values[i])
            else:
                if current_segment_times:
                    segments.append((current_segment_times, current_segment_values))
                    gaps.append((times[i-1], times[i]))
                current_segment_times, current_segment_values = [times[i]], [values[i]]

        if current_segment_times:
            segments.append((current_segment_times, current_segment_values))

        return segments, gaps

    segments = {key: split_data(*data[key]) for key in data}

    show_graphs = {'speed': True, 'rpm': True, 'collision': True}
    interval = 5

    fig, axes = plt.subplots(
        sum(show_graphs.values()), 1, figsize=(10, 15)
    )

    ax_idx = 0
    for key, show in show_graphs.items():
        if show:
            ax = axes[ax_idx] if isinstance(axes, (list, np.ndarray)) else axes
            if key == 'speed':
                ax.set_title('Truck speed')
            elif key == 'rpm':
                ax.set_title('Engine speed')
            elif key == 'collision':
                ax.set_title('CM system status')
            ax.set_ylabel(key.capitalize())
            ax.grid(True)
            for segment in segments[key][0]:
                ax.plot(segment[0], segment[1])
            for gap in segments[key][1]:
                ax.axvspan(gap[0], gap[1], color='red', alpha=0.3)
            ax.xaxis.set_major_locator(MinuteLocator(interval=interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.tick_params(axis='x')
            ax_idx += 1

    if show_graphs['collision']:
        y_ticks = [1, 3, 5, 6, 7, 8, 14]
        y_labels = ['Unavailable', 'Available', 'FCW', 'Haptic', 'FCM', 'Limited', 'Error']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.25)
    plt.show()

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