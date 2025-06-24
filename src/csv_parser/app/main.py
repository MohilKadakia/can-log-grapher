import influx_writer

from parser import CANLogParser

if __name__ == "__main__":
    filepath = "path/to/your/can_log_file.csv"  # Replace with your actual file path
    parser = CANLogParser(filepath)
    data = parser.parse()
    influx_writer.write_rows(data)
    influx_writer.write_client.close()