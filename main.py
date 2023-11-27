import os
import re
import shutil
import logging
import time
import hashlib
import sqlite3
from glob import glob


root_folder = r"C:\Users\CCrop\Documents\Tencent Files test"  # eg: X:\xxx\xxx\Tencent Files
pic_db_path = "pics.db"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
total_re_size = 0


def get_numeric_folders(root_path):  # 获取 QQ 号根路径
    numeric_folders = []
    for folder_name in os.listdir(root_path):
        if os.path.isdir(os.path.join(root_path, folder_name)):
            if re.fullmatch(r'\d+', folder_name):  # 检查文件夹名是否全为数字
                numeric_folders.append(root_path + "\\" + folder_name)
                logging.info("Find QQ number: " + folder_name)
    return numeric_folders


qqnumber_folder_root = get_numeric_folders(root_folder)
# print(qqnumber_folder_root)


def get_folder_size(folder):
    # Calculate the total size of files in the given folder.
    total_size = 0
    for root, dirs, files in os.walk(folder):
        total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
    return total_size


def format_size(size_in_bytes):
    # Convert the size from bytes to other units like KB, MB, GB, or TB.
    if size_in_bytes < 1024**2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_bytes / 1024**2:.2f} MB"
    else:
        return f"{size_in_bytes / 1024**3:.2f} GB"


def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def delete_empty_subfolders(path):
    global total_re_size
    if not os.path.isdir(path):
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # Check if the folder is empty
                folder_size = get_folder_size(dir_path)
                total_re_size += folder_size
                os.rmdir(dir_path)  # Delete the empty folder
                logging.debug(f"Del: {dir_path}, released {folder_size / 1024:.2f} Kb")
    logging.info(f"Del empty folder: {path}\\*\\")


def del_path_all(path):
    global total_re_size
    if os.path.exists(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                total_re_size += file_size
                os.remove(item_path)  # Delete file
                logging.debug(f"Del: {item_path}, released {file_size / 1024:.2f} Kb")
            elif os.path.isdir(item_path):
                folder_size = get_folder_size(item_path)
                total_re_size += folder_size
                shutil.rmtree(item_path)  # Delete folder and its contents
                logging.debug(f"Del: {item_path}, released {folder_size / 1024:.2f} Kb")
    logging.info(f"Del all: {path}\\*")


def delete_prefixed_folders(path, prefix):
    global total_re_size
    if not os.path.exists(path):
        logging.warning(f"The given path {path} does not exist.")
        return
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and item.startswith(prefix):
            folder_size = get_folder_size(item_path)
            total_re_size += folder_size
            shutil.rmtree(item_path)  # Delete dot-prefixed folder and its contents
            logging.debug(f"Del: {item_path}, released {folder_size / 1024:.2f} Kb")
    logging.info(f"Deleted folder: {path}\\")


def delete_suffixed_files(path, suffix):
    global total_re_size
    if not os.path.exists(path):
        logging.warning(f"The given path {path} does not exist.")
        return
    for root, dirs, files in os.walk(path):
        for item in files:
            file_path = os.path.join(root, item)
            if os.path.isfile(file_path) and item.endswith(suffix):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)  # 删除文件
                total_re_size += file_size
                logging.info(f"Deleted file: {file_path}, released {file_size / 1024:.2f} Kb")
    logging.debug(f"Deleted files: {path}\\{suffix}")


def delete_specific_file(file_path):
    global total_re_size
    if os.path.exists(file_path) and os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)
        os.remove(file_path)  # 删除文件
        total_re_size += file_size
        logging.info(f"Deleted file: {file_path}, released {file_size / 1024:.2f} Kb")
    else:
        logging.warning(f"File {file_path} does not exist or is not a file.")


def delete_qqnt_pics(root_path, db_file_path):
    # 连接到数据库
    conn = sqlite3.connect(db_file_path)
    c = conn.cursor()

    # 创建表 image_info，若不存在则创建
    c.execute('''CREATE TABLE IF NOT EXISTS image_info 
                 (id INTEGER PRIMARY KEY, type TEXT, md5 TEXT, size INTEGER, count INTEGER)''')

    # 创建空列表 pic_records
    pic_records = []

    # 遍历 root_path\20**-**\Ori 里的所有文件
    for file_path in glob(os.path.join(root_path, "20??-??", "Ori", "*")):
        # 计算 Ori 图片 md5 和 大小（bytes）
        md5 = calculate_md5(file_path)
        size = os.path.getsize(file_path)

        # 检查数据库中是否有相同的 md5 和大小记录
        c.execute("SELECT id, count FROM image_info WHERE md5=? AND size=?", (md5, size))
        record = c.fetchone()

        if record:
            # 如果找到记录，则更新次数
            c.execute("UPDATE image_info SET count=count+1 WHERE id=?", (record[0],))
            if record[1] + 1 > 3:
                # 如果次数 > 3，则添加到 pic_records
                pic_records.append((file_path, record[0]))
        else:
            # 若数据库找不到记录，则添加记录，次数初始为 1
            c.execute("INSERT INTO image_info (type, md5, size, count) VALUES (?, ?, ?, ?)",
                      ("Ori", md5, size, 1))

    # 提交事务
    conn.commit()
    conn.close()

    return pic_records


for i_qq_folder in qqnumber_folder_root:
    i_qq_folder = i_qq_folder + "\\nt_qq\\nt_data"

    del_path_all(i_qq_folder + "\\avatar")

    delete_prefixed_folders(i_qq_folder + "\\dataline", '.')

    delete_empty_subfolders(i_qq_folder + "\\Emoji\\marketface")
    del_path_all(i_qq_folder + "\\Emoji\\emoji-related")
    del_path_all(i_qq_folder + "\\Emoji\\emoji-recv")

    delete_prefixed_folders(i_qq_folder + "\\File", 'Thumb')

    delete_suffixed_files(i_qq_folder + "\\log", '.xlog')

    del_path_all(i_qq_folder + "\\Qzone")

    # records = delete_qqnt_pics(i_qq_folder + "\\Pic", pic_db_path)

time.sleep(0.2)
print("Total released disk space: " + str(format_size(total_re_size)))
# print(records)
