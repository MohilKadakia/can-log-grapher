import sys
import argparse
from PyQt5.QtWidgets import QApplication

from app.gui import CANLogUploader

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="An applcation to upload CAN log files to update the Grafana dashboard")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    # parser.add_argument('-vb', '--verbose', default=False, action="store_true", help="Enable verbose output")
    return parser.parse_known_args()

def main():
    app = QApplication(sys.argv)
    window = CANLogUploader()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    args = parse_arguments()
    # if args[0].verbose:
    #     print("Verbose mode enabled")
    main()