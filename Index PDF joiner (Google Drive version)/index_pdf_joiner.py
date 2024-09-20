import os
import re
import shutil
from pathlib import Path
from typing import Union

import fitz

SKIP_FILES_AND_FOLDERS_WITH = ["OLD", "DNU"]

FOLDER_IDENTIFIER = "UNQ"

FOLDER_ROOT = os.path.expanduser("~/Google Drive/Shared drives/BBG - Index cards")
SECONDARY_TARGET_FOLDER = os.path.join(Path.home(), "Desktop/Joined_PDFs")

DRUKHARI_PAGE_ORDER = [[1, 1], [1, 2], [3, 1], [2, 2], [2, 1], [1, 3], [3, 2], [2, 3], [2, 4], [4, "x"]]


def join_index_pdfs():
    folder_root = find_most_recent_folder_with_prefix(FOLDER_ROOT, FOLDER_IDENTIFIER)
    if folder_root is None:
        raise RuntimeError("Could not find working folder")
    folder_root = folder_root.rstrip(os.sep)
    project_folder = os.path.basename(folder_root)
    pattern = re.compile(re.escape(FOLDER_IDENTIFIER) + r"\d+")
    identifier = pattern.findall(project_folder)[0]
    # get folders that have PDFs
    folders_with_PDFs = find_subfolders_with_files_of_type(folder_root, ".pdf", SKIP_FILES_AND_FOLDERS_WITH)
    for folder_path in folders_with_PDFs:
        project_name = folder_path.split(os.sep)[-2].replace(" ", "_")
        target_name = folder_path.split(os.sep)[-1] + "_" + project_name + ".pdf"
        # avoid making joined PDFs of the joined PDFs
        if identifier in target_name:
            continue
        target_path_root = os.path.dirname(folder_path)
        target_file = os.path.join(target_path_root, target_name)
        files = get_files_of_type_in_folder(folder_path, ".pdf", SKIP_FILES_AND_FOLDERS_WITH)

        # skip if existing
        if os.path.isfile(target_file):
            if is_file_newer_than_files(target_file, files):
                continue
            else:
                os.remove(target_file)

        # join the PDFs
        join_pdfs(target_file, files)

        # copy the destination file
        file_copy_path = os.path.join(SECONDARY_TARGET_FOLDER, project_folder)
        if not os.path.isdir(file_copy_path):
            os.makedirs(file_copy_path)
        file_copy = os.path.join(file_copy_path, target_name)
        shutil.copy(target_file, file_copy)


def is_file_newer_than_files(file_path: str, files: list[str]) -> bool:
    this_file_ctime = os.path.getmtime(file_path)
    for file in files:
        this_ctime = os.path.getmtime(file)
        if this_ctime > this_file_ctime:
            return False
    return True


def join_pdfs(output_path: str, pdfs: list) -> None:
    """Joins the PDFs in a given list together into a given destination

    Args
    - output_path (str): full path to file
    - pdfs (list of str): full paths to files
    """
    out = fitz.open()

    drukhari = False
    for pdf in pdfs:
        if "Drukhari" in pdf:
            drukhari = True

    if drukhari:
        for file, page in DRUKHARI_PAGE_ORDER:
            file = f"0{file}"
            for pdf in pdfs:
                basename: str = os.path.basename(pdf)
                if basename.startswith(file) or basename[4:6] == file:
                    with fitz.open(pdf) as pdf_document:
                        if page != "x":
                            page -= 1  # 0-indexed
                            out.insert_pdf(pdf_document, from_page=page, to_page=page)
                        else:
                            out.insert_pdf(pdf_document)
    else:
        for file in pdfs:
            with fitz.open(file) as pdf_document:
                out.insert_pdf(pdf_document)

    # prepare page labels
    page_dict = {"startpage": 0, "style": "D", "firstpagenum": 1}
    dict_list = [page_dict]
    out.set_page_labels(dict_list)

    out.save(output_path, garbage=4, deflate=True, clean=True)
    out.close()


def get_files_of_type_in_folder(folder_path: str, file_type: str, ignore_masks: list[str] = None) -> list[str]:
    """For a given folder, gets full paths to all files within it of a given type

    Args
    - folder_path (str): The full path to the folder to be searched
    - file_type (str): The file type
    - ignore_masks (list[str], optional): Any substrings which should cause an otherwise qualified
    file to be ignored. Defaults to None.

    Returns
    - list[str]: The full paths to all the discovered files
    """
    if ignore_masks is None:
        ignore_masks = []
    files_of_type = []
    files = os.listdir(folder_path)
    for file in files:
        if file.endswith(file_type):
            skip = False
            for mask in ignore_masks:
                if mask in file:
                    skip = True
            if skip:
                continue
            file_path = os.path.join(folder_path, file)
            files_of_type.append(file_path)
    files_of_type.sort()
    return files_of_type


def find_subfolders_with_files_of_type(
    root_folder_path: str, file_type: str, ignore_masks: list[str] = None
) -> list[str]:
    if ignore_masks is None:
        ignore_masks = []
    subfolders = []
    for foldername, _, filenames in os.walk(root_folder_path):
        for filename in filenames:
            if filename.endswith(file_type):
                skip = False
                for mask in ignore_masks:
                    if mask in foldername:
                        skip = True
                if skip:
                    continue
                subfolders.append(foldername)
                break
    return subfolders


def find_most_recent_folder_with_prefix(parent_folder: str, prefix: str) -> Union[None, str]:
    """Finds the most recently created folder within the given folder
    that starts with the given prefix.

    Args
    - parent_folder (str): The path to the parent directory.
    - prefix (str): The prefix that the folder names should start with.

    Returns
    - Union[None|str]: The path of the most recently created folder that matches the criteria,
    or None if no such folder exists.
    """
    entries = os.listdir(parent_folder)

    filtered_folders = [
        entry for entry in entries if os.path.isdir(os.path.join(parent_folder, entry)) and entry.startswith(prefix)
    ]

    if not filtered_folders:
        return None

    # Find the most recently created folder
    most_recent_folder = None
    most_recent_time = None

    for folder in filtered_folders:
        folder_path = os.path.join(parent_folder, folder)
        creation_time = os.path.getctime(folder_path)
        if most_recent_time is None or creation_time > most_recent_time:
            most_recent_time = creation_time
            most_recent_folder = folder

    return os.path.join(parent_folder, most_recent_folder)


if __name__ == "__main__":
    join_index_pdfs()
