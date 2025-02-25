import psycopg2
import os
import configparser
import json
import datetime

class DatabaseOperations:
    # def __init__(self):
    #     self.db_config = {
    #         'db': os.getenv('POSTGRES_DB', 'postgres'),
    #         'user': os.getenv('POSTGRES_USER', 'postgres'),
    #         'password': os.getenv('POSTGRES_PASSWORD', '123456'),
    #         'host': os.getenv('POSTGRES_HOST', 'postgresql'),
    #         'port': os.getenv('DB_PORT', '5432')  # 也可以设置环境变量
    #     }
    def __init__(self):
        self.db_config = self.config()

    def config(self):
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.ini')
        # print(config_path)
        config = configparser.ConfigParser()
        config.read(config_path)
        return {
            'db': config['database']['db_name'],
            'user': config['database']['db_user'],
            'password': config['database']['db_password'],
            'host': config['database']['db_host'],
            'port': config['database']['db_port']
        }

    def connect(self):
        try:
            conn = psycopg2.connect(
                dbname=self.db_config['db'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                host=self.db_config['host'],
                port=self.db_config['port']
            )
            # print("连接数据库成功了！！！！")
            return conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None


    def devices_details_insert(self, devices_details):
        print("---------------------------------------------------------------------devices_details")
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()

        try:
            # 查询是否已存在设备数据
            cur.execute("""
                SELECT * FROM devices_details WHERE device_id = %s
            """, (devices_details['device_id'],))
            existing_data = cur.fetchone()

            # 提取需要保存的部分字段
            # new_devices_details = {
            #     "device_id": devices_details["device_id"],
            #     "model": devices_details["model"],  # 新增字段 model
            #     "system_version": devices_details["system_version"],  # 新增字段 system_version
            #     "device_ram": devices_details["device_ram"],  # 新增字段 device_ram
            #
            # }

            # 如果已经存在数据，则进行更新
            if existing_data:
                # 获取当前的 device_status
                device_status = devices_details.get('device_status')
                # 如果 package_list 不为空，添加到更新字段中

                # 检查 package_list 是否为空，如果为空则设置为 NULL 或 空数组
                if 'package_list' not in devices_details or not devices_details['package_list']:
                    devices_details['package_list'] = '[]'  # 空数组形式
                # 更新记录
                cur.execute("""
                                UPDATE devices_details
                                SET device_ram = %s, device_status = %s, online_time = CURRENT_TIMESTAMP, tcp_port = %s, package_list = %s
                                WHERE device_id = %s
                            """, (devices_details.get("device_ram"), device_status, devices_details.get("tcp_port"),
                                  devices_details['package_list'], devices_details['device_id']))  # 更新更多字段

                conn.commit()
                print("Device data updated successfully. ")

            else:
                # device_status = devices_details.get('device_status')
                # 如果没有记录，则插入新数据
                # details_json = json.dumps([new_devices_details])  # 将新数据放在列表中，作为初始值
                # print(devices_details["device_ram"])
                cur.execute("""
                    INSERT INTO devices_details (id, device_id, model, android_version, device_ram, online_time, device_status, tcp_port, package_list)
                    VALUES (uuid_generate_v4(), %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
                """, (
                    devices_details.get("device_id"),
                    devices_details.get("model"),
                    devices_details.get("system_version"),
                    devices_details.get("device_ram"),
                    1,
                    devices_details.get("tcp_port"),
                    devices_details['package_list']
                ))  # 插入更多字段

                conn.commit()
                print("Device data inserted successfully.")

        except Exception as e:
            conn.rollback()
            print(f"Device data.Failed to insert or update data: {e}")
        finally:
            cur.close()
            conn.close()

    def devices_info_insert(self, device_id, device_name, system_version, package_name):
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()
        try:
            # self.sync_sequence(cur)
            print("-------------------------------------------------------------------------------------------devices")
            cur.execute("""
                        INSERT INTO devices (id, device_id, device_name, created_at, ids, android_version, package_name)
                        VALUES (uuid_generate_v4(), %s, %s, CURRENT_TIMESTAMP, uuid_generate_v4(), %s, %s)
                        """, (device_id, device_name, system_version, package_name))
            conn.commit()
            print("设备数据插入成功！")
        except Exception as e:
            conn.rollback()
            print(f"Failed to insert data: {e}")
        finally:
            cur.close()
            conn.close()

    def CPU_info_insert(self, cpu_data):
        print("---------------------------------------------------------------------cpu_info")
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()

        try:
            # 查询是否已存在设备数据
            cur.execute("""
                SELECT * FROM cpu_info WHERE device_ids = %s
            """, (cpu_data['device_ids'],))
            existing_data = cur.fetchone()

            # print(f"Existing data: {existing_data}")

            # 提取需要保存的部分字段
            new_cpu_data = {
                "pid": cpu_data["pid"],
                "datetime": cpu_data["datetime"],
                "idle_rate": cpu_data["idle_rate"],
                "user_rate": cpu_data["user_rate"],
                "system_rate": cpu_data["system_rate"],
                "package_name": cpu_data["package_name"],
                "pid_cpu_rate": cpu_data["pid_cpu_rate"],
                "device_cpu_rate": cpu_data["device_cpu_rate"]
            }

            # 如果已经存在数据，则进行更新
            if existing_data:
                # print(f"Updating existing CPU data for device_ids: {cpu_data['device_ids']}")

                # 获取原有的 details 字段
                existing_details = existing_data[2] if existing_data[2] is not None else []

                # 如果 details 已经是字符串（JSON 格式），解析它
                if isinstance(existing_details, str):
                    existing_details = json.loads(existing_details)

                # print(f"Existing details list before update: {existing_details}")

                # 将新的 cpu_data 追加到现有的列表中
                existing_details.append(new_cpu_data)

                # 打印插入后的 details 列表，确认新数据是否成功添加
                # print(f"Updated details list: {existing_details}")

                # 更新记录
                cur.execute("""
                    UPDATE cpu_info
                    SET details = %s, recorded_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(existing_details), existing_data[0]))  # 传递更新后的 JSON 字符串

                conn.commit()
                print("CPU data updated successfully.")
            else:
                # 如果没有记录，则插入新数据
                # print(f"Inserting new CPU data for device_ids: {cpu_data['device_ids']}")
                details_json = json.dumps([new_cpu_data])  # 将新数据放在列表中，作为初始值

                cur.execute("""
                    INSERT INTO cpu_info (id, device_id, details, recorded_at, device_ids)
                    VALUES (uuid_generate_v4(), %s, %s, CURRENT_TIMESTAMP, %s)
                """, (cpu_data["device_id"], details_json, cpu_data["device_ids"]))

                conn.commit()
                print("CPU data inserted successfully.")

        except Exception as e:
            conn.rollback()
            print(f"CPU data.Failed to insert or update data: {e}")
        finally:
            cur.close()
            conn.close()

    def insert_meminfo(self, meminfo_data):
        print("---------------------------------------------------------------------1111111111111")
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()

        try:
            # 查询是否已存在设备数据
            cur.execute("""
                        SELECT * FROM meminfo WHERE device_ids = %s
                    """, (meminfo_data['device_ids'],))
            existing_data = cur.fetchone()

            # print(f"Existing data: {existing_data}")

            # 提取需要保存的部分字段
            new_mem_data = {
                "pid": meminfo_data["pid"],
                "datetime": meminfo_data["datetime"],
                "totalmem": meminfo_data["totalmem"],
                "freemem": meminfo_data["freemem"],
                "package_name": meminfo_data["package_name"],
                "pss": meminfo_data["pss"]
            }

            # 如果已经存在数据，则进行更新
            if existing_data:
                # print(f"Updating existing Meminfo data for device_ids: {meminfo_data['device_ids']}")

                # 获取原有的 details 字段
                existing_details = existing_data[2] if existing_data[2] is not None else []

                # 如果 details 已经是字符串（JSON 格式），解析它
                if isinstance(existing_details, str):
                    existing_details = json.loads(existing_details)

                # print(f"Existing details list before update: {existing_details}")

                # 将新的 meminfo_data 追加到现有的列表中
                existing_details.append(new_mem_data)

                # 打印插入后的 details 列表，确认新数据是否成功添加
                # print(f"Updated details list: {existing_details}")

                # 更新记录
                cur.execute("""
                            UPDATE meminfo
                            SET details = %s, recorded_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (json.dumps(existing_details), existing_data[0]))  # 传递更新后的 JSON 字符串

                conn.commit()
                print("Meminfo data updated successfully.")
            else:
                # 如果没有记录，则插入新数据
                # print(f"Inserting new Meminfo data for device_ids: {meminfo_data['device_ids']}")
                details_json = json.dumps([new_mem_data])  # 将新数据放在列表中，作为初始值

                cur.execute("""
                            INSERT INTO meminfo (id, device_id, details, recorded_at, device_ids)
                            VALUES (uuid_generate_v4(), %s, %s, CURRENT_TIMESTAMP, %s)
                        """, (meminfo_data["device_id"], details_json, meminfo_data["device_ids"]))

                conn.commit()
                print("Meminfo data inserted successfully.")

        except Exception as e:
            conn.rollback()
            print(f"Meminfo data.Failed to insert or update data: {e}")
        finally:
            cur.close()
            conn.close()

    def insert_fpsinfo(self, fps_data):
        print("---------------------------------------------------------------------fpsinfo")
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()

        try:
            # 查询是否已存在设备数据
            cur.execute("""
                        SELECT * FROM fps_info WHERE device_ids = %s
                    """, (fps_data['device_ids'],))
            existing_data = cur.fetchone()

            # print(f"Existing data: {existing_data}")

            # 提取需要保存的部分字段
            new_fps_data = {
                "datetime": fps_data["datetime"],
                "activity_window": fps_data["activity_window"],
                "fps": fps_data["fps"],
                "jank": fps_data["jank"]
            }

            # 如果已经存在数据，则进行更新
            if existing_data:
                # print(f"Updating existing FPS data for device_ids: {fps_data['device_ids']}")

                # 获取原有的 details 字段
                existing_details = existing_data[2] if existing_data[2] is not None else []

                # 如果 details 已经是字符串（JSON 格式），解析它
                if isinstance(existing_details, str):
                    existing_details = json.loads(existing_details)

                # print(f"Existing details list before update: {existing_details}")

                # 将新的 fps_data 追加到现有的列表中
                existing_details.append(new_fps_data)

                # 打印插入后的 details 列表，确认新数据是否成功添加
                # print(f"Updated details list: {existing_details}")

                # 更新记录
                cur.execute("""
                            UPDATE fps_info
                            SET details = %s, recorded_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (json.dumps(existing_details), existing_data[0]))  # 传递更新后的 JSON 字符串

                conn.commit()
                print("FPS data updated successfully.")
            else:
                # 如果没有记录，则插入新数据
                # print(f"Inserting new FPS data for device_ids: {fps_data['device_ids']}")
                details_json = json.dumps([new_fps_data])  # 将新数据放在列表中，作为初始值

                cur.execute("""
                            INSERT INTO fps_info (id, device_id, details, recorded_at, device_ids)
                            VALUES (uuid_generate_v4(), %s, %s, CURRENT_TIMESTAMP, %s)
                        """, (fps_data["device_id"], details_json, fps_data["device_ids"]))

                conn.commit()
                print("FPS data inserted successfully.")

        except Exception as e:
            conn.rollback()
            print(f"FPS data.Failed to insert or update data: {e}")
        finally:
            cur.close()
            conn.close()

    def insert_temperature(self, temperature_data):
        print("---------------------------------------------------------------------temperature")
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()

        try:
            # 查询是否已存在设备数据
            cur.execute("""
                        SELECT * FROM temperature_info WHERE device_ids = %s
                    """, (temperature_data['device_ids'],))
            existing_data = cur.fetchone()

            # print(f"Existing data: {existing_data}")

            # 提取需要保存的部分字段
            new_temperature_data = {
                "datetime": temperature_data["datetime"],
                "temperature": temperature_data["temperature"],

            }

            # 如果已经存在数据，则进行更新
            if existing_data:
                # print(f"Updating existing FPS data for device_ids: {fps_data['device_ids']}")

                # 获取原有的 details 字段
                existing_details = existing_data[2] if existing_data[2] is not None else []

                # 如果 details 已经是字符串（JSON 格式），解析它
                if isinstance(existing_details, str):
                    existing_details = json.loads(existing_details)

                # print(f"Existing details list before update: {existing_details}")

                # 将新的 fps_data 追加到现有的列表中
                existing_details.append(new_temperature_data)

                # 打印插入后的 details 列表，确认新数据是否成功添加
                # print(f"Updated details list: {existing_details}")

                # 更新记录
                cur.execute("""
                            UPDATE temperature_info
                            SET details = %s, recorded_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (json.dumps(existing_details), existing_data[0]))  # 传递更新后的 JSON 字符串

                conn.commit()
                print("temperature data updated successfully.")
            else:
                # 如果没有记录，则插入新数据
                # print(f"Inserting new FPS data for device_ids: {fps_data['device_ids']}")
                details_json = json.dumps([new_temperature_data])  # 将新数据放在列表中，作为初始值

                cur.execute("""
                            INSERT INTO temperature_info (id, device_id, details, recorded_at, device_ids)
                            VALUES (uuid_generate_v4(), %s, %s, CURRENT_TIMESTAMP, %s)
                        """, (temperature_data["device_id"], details_json, temperature_data["device_ids"]))

                conn.commit()
                print("temperature data inserted successfully.")

        except Exception as e:
            conn.rollback()
            print(f"temperature data.Failed to insert or update data: {e}")
        finally:
            cur.close()
            conn.close()

    def get_all_devices(self):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM devices;")
            devices = cur.fetchall()
            print("查看所有设备！")
            return devices
        except Exception as e:
            print(f"Failed to fetch devices: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    # 查询ids区分同设备不同时间段数据
    def get_latest_ids(self, device_id):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("""
                        SELECT ids FROM devices WHERE device_id = %s ORDER BY created_at DESC LIMIT 1;
                        """, (device_id,))
            result = cur.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"Failed to fetch ids: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_devices_details(self):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM devices_details;")
            devices = cur.fetchall()

            # 使用 str() 将 devices 转换为字符串，以便拼接
            #print("查看所有设备详细信息！" + str(devices))
            return devices
        except Exception as e:
            print(f"Failed to fetch devices: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_all_devices(self):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM devices;")
            devices = cur.fetchall()
            print("查看所有设备！")
            return devices
        except Exception as e:
            print(f"Failed to fetch devices: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_cpu_info(self, sn, ids):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("""
                    select * from cpu_info where device_ids = %s and device_id = %s
                    """, (ids, sn))
            devices = cur.fetchall()
            print("查看指定设备cpuinfo！")
            columns = [column[0] for column in cur.description]

            # 将查询结果存储为键值对形式的字典，并存储到列表中
            result = []
            for row in devices:
                row_dict = {}
                for i in range(len(columns)):
                    if isinstance(row[i], datetime.datetime):
                        row_dict[columns[i]] = row[i].strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
                    else:
                        row_dict[columns[i]] = row[i]
                result.append(row_dict)

            return result if result else []  # 返回空列表 [] 如果 result 为空
        except Exception as e:
            print(f"Failed to fetch cpuinfo: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_mem_info(self, sn, ids):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("""
                    select * from meminfo where device_ids = %s and device_id = %s
                    """, (ids, sn))
            devices = cur.fetchall()
            print("查看指定设备meminfo！")
            columns = [column[0] for column in cur.description]

            # 将查询结果存储为键值对形式的字典，并存储到列表中
            result = []
            for row in devices:
                row_dict = {}
                for i in range(len(columns)):
                    if isinstance(row[i], datetime.datetime):
                        row_dict[columns[i]] = row[i].strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
                    else:
                        row_dict[columns[i]] = row[i]
                result.append(row_dict)

            return result if result else []  # 返回空列表 [] 如果 result 为空
        except Exception as e:
            print(f"Failed to fetch memory: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_fps_info(self, sn, ids):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("""
                    select * from fps_info where device_ids = %s and device_id = %s
                    """, (ids, sn))
            devices = cur.fetchall()
            print("查看指定设备fpsinfo！")
            columns = [column[0] for column in cur.description]

            # 将查询结果存储为键值对形式的字典，并存储到列表中
            result = []
            for row in devices:
                row_dict = {}
                for i in range(len(columns)):
                    if isinstance(row[i], datetime.datetime):
                        row_dict[columns[i]] = row[i].strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
                    else:
                        row_dict[columns[i]] = row[i]
                result.append(row_dict)

            return result if result else []  # 返回空列表 [] 如果 result 为空
        except Exception as e:
            print(f"Failed to fetch fps: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_all_tablet_report(self):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM tablet_report;")
            devices = cur.fetchall()
            print("查看所有平板报告！")
            return devices
        except Exception as e:
            print(f"Failed to fetch tablet_report: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def get_tablet_report(self, report_id, sn):
        conn = self.connect()
        if not conn:
            return None
        cur = conn.cursor()
        try:
            cur.execute("""
                    select * from tablet_report where report = %s and sn = %s
                    """, (report_id, sn))
            devices = cur.fetchall()
            print("查看指定设备的平板报告！")
            columns = [column[0] for column in cur.description]

            # 将查询结果存储为键值对形式的字典，并存储到列表中
            result = []
            for row in devices:
                row_dict = {}
                for i in range(len(columns)):
                    if isinstance(row[i], datetime.datetime):
                        row_dict[columns[i]] = row[i].strftime('%Y-%m-%d %H:%M:%S')  # 转换为字符串格式
                    else:
                        row_dict[columns[i]] = row[i]
                result.append(row_dict)

            return result if result else []  # 返回空列表 [] 如果 result 为空
        except Exception as e:
            print(f"Failed to fetch tablet_report: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    # 删除指定sn和ids的性能数据
    def delete_device_data(self, sn, ids):
        print(sn)
        print(ids)
        conn = self.connect()
        if not conn:
            return None

        cur = conn.cursor()
        try:
            # Check if records exist in cpu_info table before deletion
            cur.execute("SELECT COUNT(*) FROM cpu_info WHERE device_ids IN (%s);", (ids,))
            if cur.fetchone()[0] > 0:
                cur.execute("DELETE FROM cpu_info WHERE device_ids IN (%s) and device_id IN (%s);", (ids, sn))
                print("删除 cpu_info 表中的记录")

            # Check if records exist in fps_info table before deletion
            cur.execute("SELECT COUNT(*) FROM fps_info WHERE device_ids IN (%s);", (ids,))
            if cur.fetchone()[0] > 0:
                cur.execute("DELETE FROM fps_info WHERE device_ids IN (%s) and device_id IN (%s);", (ids, sn))
                print("删除 fps_info 表中的记录")

            # Check if records exist in meminfo table before deletion
            cur.execute("SELECT COUNT(*) FROM meminfo WHERE device_ids IN (%s);", (ids,))
            if cur.fetchone()[0] > 0:
                cur.execute("DELETE FROM meminfo WHERE device_ids IN (%s) and device_id IN (%s);", (ids, sn))
                print("删除 meminfo 表中的记录")

            # Check if records exist in devices table before deletion
            cur.execute("SELECT COUNT(*) FROM devices WHERE ids IN (%s) and device_id IN (%s);", (ids, sn))
            if cur.fetchone()[0] > 0:
                cur.execute("DELETE FROM devices WHERE ids IN (%s) and device_id IN (%s);", (ids, sn))
                print("删除 devices 表中的记录")

            conn.commit()  # Commit the transaction
            print("删除相关历史数据！")

        except Exception as e:
            print(f"删除失败: {e}")
            conn.rollback()  # Rollback the transaction if something goes wrong
            return None

        finally:
            cur.close()
            conn.close()

    # 平板报告 ROM API 数据
    def insert_tablet_report(self, sn, details):
        print("---------------------------------------------------------------------tablet_report_info")
        conn = self.connect()
        if not conn:
            return
        cur = conn.cursor()

        try:

            cur.execute("""
                            INSERT INTO  tablet_report(report_id, sn, details, created_at, device_ids)
                            VALUES (uuid_generate_v4(), %s, %s, CURRENT_TIMESTAMP, uuid_generate_v4())
                        """, (sn, details))

            conn.commit()
            print("tablet report data inserted successfully.")

        except Exception as e:
            conn.rollback()
            print(f"tablet report data.Failed to insert or update data: {e}")
        finally:
            cur.close()
            conn.close()

    # def temperature_info_insert(self, device_id, battery_temp, cpu_temp):
    #     """插入温度数据"""
    #     sql = """
    #         INSERT INTO temperature_info (device_id, battery_temp, cpu_temp)
    #         VALUES (%s, %s, %s)
    #     """
    #     self.cursor.execute(sql, (device_id, battery_temp, cpu_temp))
    #     self.conn.commit()

# 测试代码
# db_operations = DatabaseOperations()
#
# # 测试连接
# conn = db_operations.connect()
#
# cpu_data = {
#     "device_id": "2528",
#     "pid": "2528",
#     "datetime": "2024-11-05 15:08:28",
#     "idle_rate": "731",
#     "user_rate": "52",
#     "system_rate": "17",
#     "package_name": "com.yangcong345.android.phone",
#     "pid_cpu_rate": "0.0",
#     "device_cpu_rate": 69,
#     "device_ids": "db18fcdb-a54c-4e16-b724-2ca7884b6b95"
# }
#
# # 调用 CPU_info_insert 方法
# d = db_operations.CPU_info_insert(cpu_data)
# print(d)
# db_operations = DatabaseOperations()
# sn = "S301YJTEST000006"
# ids = "6123430e-18cc-4884-adc7-125f36a3baa5"
# db_operations.delete_device_data(sn, ids)


