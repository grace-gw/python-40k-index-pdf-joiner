import os
import re
import shutil
from pathlib import Path
from typing import Union

import fitz

G_SKIP_FILES_AND_FOLDERS_WITH = ["OLD", "DNU"]

G_FOLDER_IDENTIFIER = "UNQ"

G_FOLDER_ROOT = os.path.expanduser("~/Google Drive/Shared drives/BBG - Index cards")
G_SECONDARY_TARGET_FOLDER = os.path.join(Path.home(), "Desktop/Joined_PDFs")


def main():
    global G_FOLDER_ROOT
    G_FOLDER_ROOT = FindMostRecentFolderWithPrefix(G_FOLDER_ROOT, G_FOLDER_IDENTIFIER)
    if G_FOLDER_ROOT is None:
        raise RuntimeError("Could not find working folder")
    G_FOLDER_ROOT = G_FOLDER_ROOT.rstrip(os.sep)
    project_folder = os.path.basename(G_FOLDER_ROOT)
    pattern = re.compile(re.escape(G_FOLDER_IDENTIFIER) + r"\d+")
    identifier = pattern.findall(project_folder)[0]
    # get folders that have PDFs
    folders_with_PDFs = FindSubfoldersWithFilesOfType(G_FOLDER_ROOT, ".pdf", G_SKIP_FILES_AND_FOLDERS_WITH)
    for folder_path in folders_with_PDFs:
        project_name = folder_path.split(os.sep)[-2].replace(" ", "_")
        target_name = folder_path.split(os.sep)[-1] + "_" + project_name + ".pdf"
        # avoid making joined PDFs of the joined PDFs
        if identifier in target_name:
            continue
        target_path_root = os.path.dirname(folder_path)
        target_file = os.path.join(target_path_root, target_name)
        # skip if existing
        if os.path.isfile(target_file):
            continue

        files = GetFilesOfTypeInFolder(folder_path, ".pdf", G_SKIP_FILES_AND_FOLDERS_WITH)
        # join the PDFs
        JoinPDFs(target_file, files)

        # copy the destination file
        file_copy_path = os.path.join(G_SECONDARY_TARGET_FOLDER, project_folder)
        if not os.path.isdir(file_copy_path):
            os.makedirs(file_copy_path)
        file_copy = os.path.join(file_copy_path, target_name)
        shutil.copy(target_file, file_copy)


def JoinPDFs(destinationPDF: str, PDFs: list) -> None:
    """Joins the PDFs in a given list together into a given destination

    Args:
    - destinationPDF (str): full path to file
    - PDFs (list of str): full paths to files
    """
    out = fitz.open()

    for file in PDFs:
        temp_page = fitz.open(file)
        out.insert_pdf(temp_page)

    # prepare page labels
    page_dict = {"startpage": 0, "style": "D", "firstpagenum": 1}
    dict_list = [page_dict]
    out.set_page_labels(dict_list)

    out.save(destinationPDF, garbage=4, deflate=True, clean=True)
    out.close()


def GetFilesOfTypeInFolder(folderPath: str, fileType: str, ignoreMasks: list[str] = []) -> list[str]:
    files_of_type = []
    files = os.listdir(folderPath)
    for file in files:
        if file.endswith(fileType):
            skip = False
            for mask in ignoreMasks:
                if mask in file:
                    skip = True
            if skip:
                continue
            file_path = os.path.join(folderPath, file)
            files_of_type.append(file_path)
    files_of_type.sort()
    return files_of_type


def FindSubfoldersWithFilesOfType(rootFolderPath: str, fileType: str, ignoreMasks: list[str] = []) -> list[str]:
    subfolders = []
    for foldername, _, filenames in os.walk(rootFolderPath):
        for filename in filenames:
            if filename.endswith(fileType):
                skip = False
                for mask in ignoreMasks:
                    if mask in foldername:
                        skip = True
                if skip:
                    continue
                subfolders.append(foldername)
                break
    return subfolders


def FindMostRecentFolderWithPrefix(v_parentFolder: str, v_prefix: str) -> Union[None, str]:
    """Finds the most recently created folder within the given folder
    that starts with the given prefix.

    Parameters:
    v_parentFolder (str): The path to the parent directory.
    v_prefix (str): The prefix that the folder names should start with.

    Returns:
    Union[None|str]: The path of the most recently created folder that matches the criteria,
    or None if no such folder exists.
    """
    entries = os.listdir(v_parentFolder)

    filtered_folders = [
        entry for entry in entries if os.path.isdir(os.path.join(v_parentFolder, entry)) and entry.startswith(v_prefix)
    ]

    if not filtered_folders:
        return None

    # Find the most recently created folder
    most_recent_folder = None
    most_recent_time = None

    for folder in filtered_folders:
        folder_path = os.path.join(v_parentFolder, folder)
        creation_time = os.path.getctime(folder_path)
        if most_recent_time is None or creation_time > most_recent_time:
            most_recent_time = creation_time
            most_recent_folder = folder

    return os.path.join(v_parentFolder, most_recent_folder)


if __name__ == "__main__":
    main()
