import datetime
import os

def convert_timestamp(log_file):
    # Generate the output file name
    base, ext = os.path.splitext(os.path.basename(log_file))
    dir_name = os.path.dirname(log_file)
    output_file = os.path.join(dir_name, f"{base}_converted{ext}")
    
    # Check if the output file already exists and add a numeric suffix if necessary
    counter = 1
    while os.path.exists(output_file):
        output_file = os.path.join(dir_name, f"{base}_converted_{counter}{ext}")
        counter += 1
    
    with open(log_file, 'r') as infile:
        lines = infile.readlines()
    
    new_lines = []
    for line in lines:
        # Extract the timestamp
        timestamp_str = line.split(' ')[0].strip('()')
        timestamp = float(timestamp_str)
        
        # Convert to human-readable format in GMT
        human_readable_time = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        
        # Replace the timestamp in the original line
        new_line = line.replace(f'({timestamp_str})', f'({human_readable_time})')
        new_lines.append(new_line)
    
    with open(output_file, 'w') as outfile:
        outfile.writelines(new_lines)
    
    print(f"Converted file saved as: {output_file}")

def convert_all_timestamps_in_directory(directory):
    files_converted = False
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt') and not file.endswith('_converted.txt'):
                log_file = os.path.join(root, file)
                converted_file = os.path.join(root, f"{os.path.splitext(file)[0]}_converted.txt")
                if os.path.exists(converted_file):
                    print(f"File already converted: {log_file}")
                    continue
                print(f"Converting file: {log_file}")
                convert_timestamp(log_file)
                files_converted = True
    
    if not files_converted:
        print("No files to convert in the directory.")

if __name__ == "__main__":
    base_directory = os.path.dirname(__file__)
    convert_all_timestamps_in_directory(base_directory)