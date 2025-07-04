import numpy as np
import pandas as pd
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import mplcursors
# import plotly.express as px

from scipy import signal

def lpf(data, cuttoff_freq, btype='lowpass'):
    sample_rate = 1/(data.index[1] - data.index[0])  # Assuming uniform sampling
    cuttoff_freq = min(0.8*sample_rate / 2, cuttoff_freq)  # Nyquist frequency1
    # print(f"Sample rate: {sample_rate}")
    order = 2
    sos = signal.butter(order, cuttoff_freq, fs=sample_rate, btype=btype, analog=False, output='sos')
    filtered_data = signal.sosfiltfilt(sos, data)
    return pd.Series(filtered_data, index=data.index, name=data.name)


def parse_args():
    parser = argparse.ArgumentParser(description="Process CAN log")
    parser.add_argument('-s', '--src_file', nargs='?', default=[], action="append", type=Path, help="CAN log file (csv) to be read in")
    parser.add_argument('-d', '--dir', nargs='?', default=[], action="append", type=Path, help="Directory containing CAN log files (csv) to be read in")
    parser.add_argument('-f', '--filter', action=argparse.BooleanOptionalAction,  help="Run the spikey CAN signals through a despiking filter")
    parser.add_argument('-a', '--add', default=[], action="append", help="CAN signals to be included in analysis")
    parser.add_argument('-r', '--regex', default=[], action="append", help="CAN signals to be included in analysis (regexed)")
    parser.add_argument('-i', '--highlight',  action=argparse.BooleanOptionalAction, help="Highlight on hover")
    parser.add_argument('-n', '--inv-fault', action=argparse.BooleanOptionalAction, help="Plot the inverter fault output")


    return parser.parse_args()


def parse_csv(file_path: Path) -> pd.DataFrame:
    def parse_data(data: str):
        try:
            return float(data)
        except ValueError:
            return data
        
    def parse_time(t):
        if "." in str(t):
            return float(t)
        else:
            return float(int(t, 16)) / 1000
    df = pd.read_csv(file_path, header=None,
                     names=['t', 'sig', 'data'], index_col='t',
                    #  converters={'t': lambda x: float(int(x, 16)) / 1000, 'sig': lambda x: x.strip(), 'data': parse_data})  # convert timestamp in hex to float
                     converters={'t': parse_time, 'sig': lambda x: x.strip(), 'data': parse_data})  # convert timestamp in hex to float
    return df



# How many samples to run the FBEWMA over.
SPAN = 10



def ewma_fb(df_column, span):
    ''' Apply forwards, backwards exponential weighted moving average (EWMA) to df_column. '''
    # Forwards EWMA.
    fwd = df_column.ewm(span=span).mean()
    # Backwards EWMA.
    bwd = df_column[::-1].ewm(span=10).mean()
    # Add and take the mean of the forwards and backwards EWMA.
    fb_ewma = (fwd + bwd[::-1]) / 2
    return fb_ewma


def unspike(y, N=1):
    for _ in range(N):
        std = y.std()
        mean = y.mean()
        clipped = y[y.between(mean - std, mean + std)]
        ewma = ewma_fb(clipped, SPAN)

        c_e = np.abs(clipped - ewma)
        cutoff = c_e.mean() - c_e.std()
        rm_outliers = clipped[c_e > cutoff]

        y = rm_outliers.infer_objects(copy=False).interpolate()
    
    return y

WHEEL_DIAMETER_M = 16 * 2.54 / 100
GEAR_RATIO_MOT_TO_WHEEL = 4
WHEEL_CIRCUMFRENCE = WHEEL_DIAMETER_M * np.pi
M_TO_KM = 1000
MIN_PER_HR = 60

RPM_TO_KPH = (WHEEL_CIRCUMFRENCE / GEAR_RATIO_MOT_TO_WHEEL) / M_TO_KM * MIN_PER_HR

if __name__ == "__main__":
    # Read the CSV file
    args = parse_args()
    df = pd.DataFrame()
    start_time = 0
    if args.src_file:
        for csv_file in args.src_file:
            df = pd.concat([df, parse_csv(csv_file)])
    if args.dir:
        start_time = df.index[-1] if not df.empty else 0
        for dir_path in args.dir:
            for csv_file in dir_path.glob("*.csv"):
                df = pd.concat([df, parse_csv(csv_file).shift(start_time)])

    if args.inv_fault:
        # Add inverter fault output
        args.add.append('INV_Post_Fault_Hi')
        args.add.append('INV_Post_Fault_Lo')
        args.add.append('INV_Run_Fault_Hi')
        args.add.append('INV_Run_Fault_Lo')
        


    mask1 = df['sig'].str.contains('|'.join(map(lambda x: f"^{x}$", args.add)), regex=True) if args.add else pd.Index([False] * len(df))
    mask2 = df['sig'].str.contains('|'.join(args.regex), regex=True) if args.regex else pd.Index([False] * len(df))

    df = df[mask1 | mask2]


    df.sort_index(inplace=True)
    
    # Plotting code can be added here
    # For example, using matplotlib or seaborn to create visualizations
    fig, ax = plt.subplots()
    lines = []
    labels = []
    for sig in sorted(df['sig'].unique()):
        y = df[df['sig'] == sig]['data']
        if sig == 'INV_Motor_Speed':
            y = y * RPM_TO_KPH
            sig = 'INV_Motor_Speed (kph)'
        if args.filter:
            unspiked = unspike(y,1)
            # unspiked = lpf(y, 1000)
            line, = ax.plot(unspiked, marker='.', label=f'{sig}')
        else:
            line, = ax.plot(y, marker='.', label=f'{sig}')
        lines.append(line)
        labels.append(sig)


    if args.highlight:
        cursor = mplcursors.cursor(lines, hover=mplcursors.HoverMode.Transient)
        # cursor.connect("add", lambda sel: sel.annotation.set_text(labels[sel.index]))
    plt.xlabel('Time (s)')
    plt.ylabel('Data')
    plt.title('CAN Signals')
    plt.grid()
    plt.legend()
    plt.show()
