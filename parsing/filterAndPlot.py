import csv
import sys
import matplotlib.pyplot as plt
from math import pi
import re

WHEEL_DIAMETER_M = 16 * 2.54 / 100
GEAR_RATIO_MOT_TO_WHEEL = 3.75
WHEEL_CIRCUMFRENCE = WHEEL_DIAMETER_M * pi
M_TO_KM = 1000
MIN_PER_HR = 60

RPM_TO_KPH = (WHEEL_CIRCUMFRENCE / GEAR_RATIO_MOT_TO_WHEEL) / M_TO_KM * MIN_PER_HR 

pattern = r"LOGS(\d+)_parsed\.txt"

# Define the conversion formula for the third column
def convert_third_column_value(original_value):
    return original_value * RPM_TO_KPH

# Convert hexadecimal time (ms) to seconds
def convert_time_to_seconds(hex_time):
    time_in_ms = int(hex_time, 16)  # Convert hex to int
    time_in_seconds = time_in_ms / 1000.0  # Convert ms to seconds
    return time_in_seconds

# Write the filtered data to a CSV file
def write_to_csv(output_file, times, values):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (seconds)', 'Value'])  # Writing header
        for time, value in zip(times, values):
            writer.writerow([time, value])

# Example:
# python filterAndPlot.py ..\logs\August31Testing\parsed\LOGS4_Julian_twoRunsHardAccel_parsed.txt INV_Motor_Speed yes

# Main function
def main(input_file, signal_to_plot):
    # Lists to hold the filtered and converted data for plotting
    times = []
    values = []

    print(f"input_file: {input_file}")
    print(signal_to_plot)

    signalFound = False

    # Process the file
    with open(input_file, mode='r') as infile:
        reader = csv.reader(infile)
        
        for row in reader:
            signal_name = row[1]  # Get the signal name from the second column
            # print(signal_name)

            # print(f"{signal_name} == {signal_to_plot}")

            if signal_name.strip() == signal_to_plot.strip():
                signalFound = True
                # Convert the first column (hex time to seconds)
                time_in_seconds = convert_time_to_seconds(row[0])
                times.append(time_in_seconds)

                # Convert the third column based on the custom formula
                original_value = float(row[2])  # float
                # print(original_value)
                if signal_to_plot == "INV_Motor_Speed":
                    # print("converting speed")
                    converted_value = convert_third_column_value(original_value)
                    values.append(converted_value)
                else:
                    values.append(original_value)

        if signalFound is False:
            print("Signal not found!")
            sys.exit()

    # Write the filtered and converted data to a new CSV file
    if create_csv.strip() == "yes":
        match = re.search(pattern, input_file)
        log_file = match.group(1)  # Extract the number part
        output_file = f"LOG_{log_file}_{signal_to_plot}_filtered_data.csv"
        write_to_csv(output_file, times, values)
        print(f"Filtered data written to {output_file}")

    # Plotting the data
    plt.figure(figsize=(10, 6))
    plt.plot(times, values, marker='o', linestyle='-', color='b')

    # Adding titles and labels
    plt.title(f'{signal_to_plot} vs Time')
    plt.xlabel('Time (seconds)')
    plt.ylabel(signal_to_plot)

    # Show the plot
    plt.grid(True)
    plt.show()

# Check if the script is being run directly
if __name__ == "__main__":
    # Example: python filterAndPlot.py INV_Motor_Speed
    # Ensure the user provided the correct number of arguments
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_file> <signal_name> <create_CSV[yes|no]>")
        sys.exit(1)

    # Get the input file path and signal name from the command-line arguments
    input_file = sys.argv[1]
    signal_to_plot = sys.argv[2]
    create_csv = sys.argv[3]

    # Call the main function with the provided signal name
    main(input_file, signal_to_plot)