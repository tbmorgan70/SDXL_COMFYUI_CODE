import subprocess
import glob

# Path to your PNG folder
png_folder = "C:\Users\tbmor\Desktop\Nova_Weird"
png_files = glob.glob(f'{png_folder}/*.png')

# Path to exiftool in your repo
exiftool_path = "C:\\Users\\tbmor\\Desktop\\CODE\\EXTERNAL CODE BASES\\exiftool"
for file in png_files:
    subprocess.run(['perl', exiftool_path, '-all=', '-overwrite_original', file])