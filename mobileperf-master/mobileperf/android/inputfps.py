from fpslis import IFpsListener
from datetime import datetime
import csv
import os
import configparser
from DB_utils import DatabaseOperations
# from mobileperf.common.log import logger

class FpsListenserImpl(IFpsListener):
    def __init__(self):
        self.package = self.get_package_from_config()

    @staticmethod
    def get_parent_directory(path, levels=1):
        for _ in range(levels):
            path = os.path.dirname(path)
        return path

    def identify_directory_name(self, base_dir):
        # Traverse self.package directory for subdirectories
        for dir_name in os.listdir(base_dir):
            dir_path = os.path.join(base_dir, dir_name)
            if os.path.isdir(dir_path):  # Ensure it's a directory
                return dir_name  # Return the first directory name found
        return None

    def get_package_from_config(self):
        config = configparser.ConfigParser()
        config.read('config.conf')
        return config.get('Common', 'package', fallback='default_package')

    def report_fps_info(self, fps_info, devices):
        print('\n')
        print("Current Device:", devices)
        print("Current Process:", str(fps_info.pkg_name))
        print("Current Window:", str(fps_info.window_name))
        print("Window Refresh Time:", str(fps_info.time))
        print("FPS:", str(fps_info.fps))
        print("Total Frames in 2s:", str(fps_info.total_frames))
        print("Frames Dropped (>16.67ms):", str(fps_info.jankys_more_than_16))
        print(fps_info.jankys_ary)
        print("Severe Jank (>166.7ms):", str(fps_info.jankys_more_than_166))
        print('\n')

        # Dynamically get the base path (assuming the script is in the project root)
        base_path = os.path.dirname(os.path.abspath(__file__))
        target_dir = FpsListenserImpl.get_parent_directory(base_path, levels=3)
        source_mobileperf_folder = os.path.join(target_dir)

        target_device_id = devices.replace(':', '_').replace('.', '_')
        package_dir = os.path.join(source_mobileperf_folder, "R", f"_{target_device_id}", "results", self.package)
        identified_dir_name = self.identify_directory_name(package_dir)

        if identified_dir_name:
            file_path = os.path.join(package_dir, identified_dir_name, "fps_data.csv")
            print(f"FPS Data File Path: {file_path}")
        else:
            print("No subdirectory found")
            return

        # Check if file exists and is empty
        file_exists = os.path.isfile(file_path)
        is_empty = not file_exists or os.stat(file_path).st_size == 0

        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            if is_empty:
                writer.writerow(["datetime", "activity window", "fps", "jank"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                str(fps_info.pkg_name) + "/" + str(fps_info.window_name),
                int(fps_info.fps),
                str(fps_info.jankys_more_than_166)
            ])
        try:
            # 数据库连接实例化
            db_operations = DatabaseOperations()

            # 查询新ids，用于区分新老数据
            latest_ids = db_operations.get_latest_ids(devices)
            # Prepare fps_data for insertion into database
            fps_data = {
                'device_id': devices,
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'activity_window': str(fps_info.pkg_name) + "/" + str(fps_info.window_name),
                'fps': int(fps_info.fps),
                'jank': str(fps_info.jankys_more_than_166),
                'device_ids': latest_ids
            }

            # Insert fps_info into the database
            db_operations.insert_fpsinfo(fps_data)

        except Exception as db_e:
            print(f"Failed to insert FPS data into database: {db_e}")