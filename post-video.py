import logging
import os
import pickle
import ping
import time
from stat import S_ISREG, ST_MTIME, ST_MODE
import ffmpy
from telegram.ext import Updater
import configparser


config = configparser.ConfigParser()
config.read('settings.ini')

FORMAT = '%(asctime)-15s:%(levelname)s:%(message)s'
logging.basicConfig(filename=config["SETTINGS"]["log_filename"], level=logging.INFO, format=FORMAT)
token = config["SETTINGS"]["telegram_token"]
channel = config["SETTINGS"]["telegram_channel"]
direcory_path = config["SETTINGS"]["video_folder"]



def GetVideosFromFileSystem():
    entries = (os.path.join(direcory_path, fn) for fn in os.listdir(direcory_path))
    entries = ((os.stat(path), path) for path in entries)
    entries = ((stat[ST_MTIME], path)
               for stat, path in entries if S_ISREG(stat[ST_MODE]))
    return entries


def RemoveFileIfExist(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print('File does not exists')


def CreateWorkingDirectory(temporary_directory):
    try:
        os.mkdir(temporary_directory)
        logging.info("Directory ", temporary_directory, " created ")
    except FileExistsError:
        logging.debug("Directory ", temporary_directory, " exists")

        
def SaveToCache(cache_file, filesUploaded):
    with open(cache_file, 'wb') as f:
        cacheFiles = files[:1]+filesUploaded
        pickle.dump(cacheFiles, f)

temporary_directory = direcory_path + "tmp/"
cache_file = temporary_directory + "cache.dat"
files = []


CreateWorkingDirectory(temporary_directory)


for cdate, path in sorted(GetVideosFromFileSystem()):
    files.append((time.ctime(cdate), os.path.basename(path)))

sorted(files, key=lambda x: x[0])
files = list(map(lambda x: x[1], files))

try:
    with open(cache_file, 'rb') as f:
        filesUploaded = pickle.load(f)
except Exception:
    logging.warning("cache file is broken")
    filesUploaded = []

files = list(filter(lambda x: str(x).endswith(".mp4") or str(x).endswith(".webm"), files))
files = list(filter(lambda x: x not in filesUploaded, files))

currentRawFile = str(direcory_path + str(files[0]))


try:
    if currentRawFile.endswith(".webm"):
        ffmpeg_output = str(direcory_path + "tmp/" + str(files[0])).replace(".webm", ".mp4")
        RemoveFileIfExist(ffmpeg_output)
        ff = ffmpy.FFmpeg(inputs={currentRawFile: None},outputs={ffmpeg_output: None})
        ff.run()
        currentRawFile = ffmpeg_output

    logging.info(currentRawFile)
    ping.WaitUntilInternetWillAvailable()
except:
    logging.critical("telegram convert failed. Skipping file")
    SaveToCache(cache_file, filesUploaded)
    exit()

try:
    updater = Updater(token=token, request_kwargs={'read_timeout': 1000, 'connect_timeout': 1000})
    updater.bot.send_video(chat_id=channel, video=open(currentRawFile, 'rb'), supports_streaming=True)
    logging.info("telegram push successful")
    SaveToCache(cache_file, filesUploaded)
except:
    logging.critical("telegram push failed")


