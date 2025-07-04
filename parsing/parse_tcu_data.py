import sys
import os
import cantools
from pathlib import Path
import concurrent.futures

def process_message(message: str, fileName) -> tuple:
    if len(message) < 17 or message[8] != 'x':
        print('Error: CAN Format seems wrong in' + fileName + '! Skipping line')
        # sys.exit()
    else:
        timestamp = float(int(message[:8], 16)) / 1000
        clean_hex = message[9:]

        id_hex = clean_hex[:8]
        data_hex = clean_hex[8:]

        id_int = int(id_hex, 16)
        return timestamp, id_int, data_hex

def run_script(folder_path: Path, filepath: Path):
    db = cantools.database.load_file('2024CAR.dbc')
    fileName = filepath.name
    print(f"Parsing file: {filepath}")

    # Create the directory to store the parsed files
    output_folder = Path("parsed_files")
    output_folder.mkdir(parents=True, exist_ok=True)

    # Flag to track if any lines were skipped
    skipped_any = False

    # keep same dir structure as input folder
    parsed_file_path = output_folder / filepath.relative_to(folder_path).with_suffix('.csv')
    skipped_file_path = output_folder / filepath.relative_to(folder_path).with_suffix('.skipped.txt')

    parsed_file_path.parent.mkdir(parents=True, exist_ok=True)
    skipped_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'r') as input_file, open(parsed_file_path, 'w') as output_file, open(skipped_file_path, 'w') as skipped_file:
        for line in input_file:
            if len(line.strip()) < 17 or 'x' not in line.strip()[:9]:
                skipped_file.write(line)
                skipped_any = True
                continue
            try: 
                timestamp, can_id, can_data = process_message(line.strip(), fileName)
            except:
                print(f"File with wrong format: {parsed_file_path}")
                print(f"Line: {line}")

            # if can_id == 218103553:
            #     skipped_file.write(line)
            #     skipped_any = True
            #     continue

            try:
                msg = db.get_message_by_frame_id(can_id)
            except KeyError:
                skipped_file.write(line)
                skipped_any = True
                continue

            try: 
                data_bytes = bytes.fromhex(can_data)
                decoded_signals = msg.decode(data_bytes)
            except:
                skipped_file.write(line)
                skipped_any = True
                continue

            for signal in decoded_signals:
                output_file.write(f'{timestamp}, {signal}, {decoded_signals[signal]}\n')
    
    # Check if no lines were skipped and delete the skipped file if it's empty
    if not skipped_any:
        os.remove(skipped_file_path)

if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print('Usage: python3 parse_tcu_data.py <path_to_file>')
        sys.exit()
    if len(sys.argv) == 3:
        if sys.argv[2] == "-All":
            # example: python3 parse_tcu_data.py <pathToFolder> -All
            folder_path = Path(sys.argv[1])
            files = list(folder_path.rglob('*.TXT'))

            # exit()
            # Get the number of files
            print(f"Number of files: {len(files)}")
            # for file_path in files:
            #     print(f"Processing file: {file_path}")
            #     run_script(folder_path, file_path)
            with concurrent.futures.ProcessPoolExecutor() as executor:
                for file_path in files:
                    executor.submit(run_script, folder_path, file_path)
    else:
        run_script(sys.argv[1])
