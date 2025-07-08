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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dbc_path = os.path.join(script_dir, '2024CAR.dbc')
    db = cantools.database.load_file(dbc_path)
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
    return parsed_file_path

def parse_raw_folder(folder_path: str):
    """
    Parse all raw .TXT files in a folder and return paths to generated CSV files.
    
    Args:
        folder_path: Path to folder containing raw files
        
    Returns:
        List of paths to the generated CSV files
    """
    folder = Path(folder_path)
    files = list(folder.rglob('*.TXT'))
    output_paths = []
    
    print(f"Number of files: {len(files)}")
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for file_path in files:
            futures.append(executor.submit(run_script, folder, file_path))
        
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            output_paths.append(future.result())
    
    return output_paths
def parse_raw_file(file_path: str):
    """
    Parse a single raw .TXT file and return the path to the generated CSV file.
    
    Args:
        file_path: Path to the raw file
        
    Returns:
        Path to the generated CSV file
    """
    file_path = Path(file_path)
    folder_path = file_path.parent
    
    # Use the existing run_script function to process the file
    result_path = run_script(folder_path, file_path)
    
    return result_path

if __name__ == '__main__':
    # This code runs when the script is executed directly (not imported)
    if len(sys.argv) > 1:
        # Command-line usage still works
        if len(sys.argv) == 3 and sys.argv[2] == "-All":
            # Process entire folder
            folder_path = sys.argv[1]
            result_paths = parse_raw_folder(folder_path)
            print(f"Generated {len(result_paths)} CSV files")
        else:
            # Process single file
            folder_path = Path(os.path.dirname(sys.argv[1]))
            file_path = Path(sys.argv[1])
            result_path = run_script(folder_path, file_path)
            print(f"Generated CSV file: {result_path}")
    else:
        # No arguments provided
        print("Usage:")
        print("  python parse_tcu_data.py <path_to_file>")
        print("  python parse_tcu_data.py <path_to_folder> -All")
        print("\nThis script can also be imported and used programmatically:")
        print("  from parsing.raw_parsing.parse_tcu_data import parse_raw_folder")
        print("  result_paths = parse_raw_folder(folder_path)")
