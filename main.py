import os
import re
import shutil

root_folder = r"C:\Users\CCrop\Documents\Tencent Files"  # eg: X:\xxx\xxx\Tencent Files


def get_numeric_folders(root_path):
    numeric_folders = []
    for folder_name in os.listdir(root_path):
        if os.path.isdir(os.path.join(root_path, folder_name)):
            if re.fullmatch(r'\d+', folder_name):  # 检查文件夹名是否全为数字
                numeric_folders.append(root_path + "\\" + folder_name)
    return numeric_folders


def delete_empty_subfolders(path):
    if not os.path.isdir(path):
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # 检查文件夹是否为空
                os.rmdir(dir_path)  # 删除空文件夹
    print(f"Del empty folder: {path}\\*")


def del_path_all(path):
    if os.path.exists(path):
        # 遍历目录中的所有内容
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)  # 删除文件
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 删除文件夹及其所有内容
    print(f"Del all: {path}\\*")


def delete_dot_prefixed_folders(path):
    if not os.path.exists(path):
        print(f"The given path {path} does not exist.")
        return
    # 遍历目录中的所有内容
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and item.startswith('.'):
            shutil.rmtree(item_path)  # 删除以点开头的文件夹及其所有内容
    print(f"Deleted folder: {path}\\.*")

qqnumber_folder_root = get_numeric_folders(root_folder)

print(qqnumber_folder_root)
# progress "nt_data" folder
