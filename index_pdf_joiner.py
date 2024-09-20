import os
import shutil
from pathlib import Path

import fitz

G_FOLDER_ROOT = "/Volumes/Repro/W.I.P/BOOK PRODUCTION/40K_Web/UNQ0203_Index_Cards_web/"
G_SECONDARY_TARGET_FOLDER = os.path.join(Path.home(),"Desktop/Joined_PDFs")

def main():
	global G_FOLDER_ROOT
	G_FOLDER_ROOT = G_FOLDER_ROOT.rstrip(os.sep)
	project_folder = os.path.basename(G_FOLDER_ROOT)
	# get folders that have PDFs
	folders_with_PDFs = FindSubfoldersWithFilesOfType(G_FOLDER_ROOT,".pdf")
	for folder_path in folders_with_PDFs:
		project_name = folder_path.split(os.sep)[-2]
		target_name = folder_path.split(os.sep)[-1] + "_" + project_name + ".pdf"
		# avoid making joined PDFs of the joined PDFs
		if "UNQ0203" in target_name:
			continue
		target_path_root = os.path.dirname(folder_path)
		target_file = os.path.join(target_path_root,target_name)
		# skip if existing
		if os.path.isfile(target_file):
			continue

		files = GetFilesOfTypeInFolder(folder_path,".pdf")
		# join the PDFs
		JoinPDFs(target_file,files)

		# copy the destination file
		file_copy_path = os.path.join(G_SECONDARY_TARGET_FOLDER,project_folder)
		if not os.path.isdir(file_copy_path):
			os.makedirs(file_copy_path)
		file_copy = os.path.join(file_copy_path,target_name)
		shutil.copy(target_file,file_copy)

def JoinPDFs(destinationPDF: str, PDFs: list) -> None:
	"""Joins the PDFs in a given list together into a given destination

	Args:
		destinationPDF (str): full path to file
		PDFs (list of str): full paths to files
	"""
	out = fitz.open()

	for file in PDFs:
		temp_page = fitz.open(file)
		out.insert_pdf(temp_page)

	# prepare page labels
	page_dict = {'startpage': 0, 'style': 'D', 'firstpagenum': 1}
	dict_list = [page_dict]
	out.set_page_labels(dict_list)

	out.save(destinationPDF)

def GetFilesOfTypeInFolder(folderPath: str, fileType: str) -> list[str]:
	files_of_type = []
	files = os.listdir(folderPath)
	for file in files:
		if file.endswith(fileType):
			file_path = os.path.join(folderPath,file)
			files_of_type.append(file_path)
	files_of_type.sort()
	return files_of_type

def FindSubfoldersWithFilesOfType(rootFolderPath: str, fileType: str) -> list[str]:
	subfolders = []
	for foldername, _, filenames in os.walk(rootFolderPath):
		for filename in filenames:
			if filename.endswith(fileType):
				subfolders.append(foldername)
				break
	return subfolders

if __name__ == '__main__':
	main()