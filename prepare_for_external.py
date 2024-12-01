import os
import os.path
import shutil, json
import pandas as pd
from multiprocessing import Pool
import unicodedata
import subprocess
from time import sleep
from datetime import datetime
from io import StringIO
import sys

MUSIC="D:/IU-OneDrive/OneDrive - Indiana University/Music"
MUSIC_STAGE_DIR = "F:/temp/music"
LOGS = "./logs"

def make_pool():
  return Pool(12)

def ffprobe():
  if sys.platform == "win32":
    return "C:/ffmpeg/bin/ffprobe.exe"
  elif sys.platform == "linux":
    return "ffprobe"
  else:
    raise Exception(f"No ffprobe on platform '{sys.platform}'")

def ffmpeg():
  if sys.platform == "win32":
    return "ffmpeg"
  elif sys.platform == "linux":
    return "ffmpeg"
  else:
    raise Exception(f"No ffprobe on platform '{sys.platform}'")

def clear_logs():
  shutil.rmtree(LOGS, ignore_errors=True)
  os.makedirs(LOGS, exist_ok=True)

def open_log(name):
  pth, ext = os.path.splitext(name)
  return open(os.path.join(LOGS, pth+".log"), 'a', encoding="utf-8")
def write_log(name, msg):
  with open_log(name) as l:
    l.write(msg)
    l.write("\n")

def remove_accents(input_str):
  input_str = os.path.abspath(input_str)
  folder_pth, name = os.path.split(input_str)
  
  #nfkd_form = unicodedata.normalize('NFKC', name)
  #new_name = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
  new_name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
  new_name = new_name.replace('ß', "ss").replace('é', 'e').replace('ê', 'e').replace('â', 'a').replace('\\', '/').replace('ü', 'u').replace('ö', 'o').replace('ä', 'a').replace('ë', 'e').replace('ï', 'i')
  #new_name = new_name.replace('\\', '/')
  new_full_name = os.path.join(folder_pth, new_name)
  #print(input_str, new_full_name)
  #print("\n")
    #exit()
  if input_str != new_full_name:
    shutil.move(input_str, new_full_name)
    sleep(0.5)
    #print(input_str, new_name)
  return new_full_name

SHRINK_SIZE_MB=7.0
SKIP_DUR_SEC=20*60
MAX_BITRATE=120_000.0
def file_size_mb(path):
  return os.path.getsize(path) / (1024*1024)

def ffmpeg_probe(path):
    with open_log(os.path.basename(path)) as log, StringIO() as buf:
      p = subprocess.Popen([ffprobe(), '-of', 'json', '-show_streams', '-show_format', path], stdout=subprocess.PIPE, stderr=log, shell=False, bufsize=1, universal_newlines=True, encoding="utf-8")
      for line in p.stdout:
          log.write(line)
          buf.write(line)
      output = buf.getvalue()
      _out, err = p.communicate()
      if p.returncode != 0:
        raise Exception('ffprobe', output, err)
      return json.loads(output)

def ffprobe_bitrate(path):
  with open_log(os.path.basename(path)) as log, StringIO() as buf:
    p = subprocess.Popen([ffprobe(), "-select_streams", "a:0", "-show_entries", "stream=bit_rate", "-of", "compact=p=0:nk=1", path], stdout=subprocess.PIPE, stderr=log, shell=False, bufsize=1, universal_newlines=True, encoding="utf-8")
    for line in p.stdout:
      log.write(line)
      buf.write(line)
    output = buf.getvalue()
    _out, err = p.communicate()
    if p.returncode != 0:
      raise Exception('ffprobe', output, err)
    return float(output)

def ffmpeg_resize(src, dest, bitrate):
  overwrite = False
  if src == dest:
    overwrite = True
    pth, ext = os.path.splitext(dest)
    dest =  pth + ".tmp" + ext
  with open_log(os.path.basename(src)) as log, StringIO() as buf:
    p = subprocess.Popen([ffmpeg(), '-y', '-i', src, "-b:a", str(int(bitrate)), dest], stdout=subprocess.PIPE, stderr=log, shell=False, bufsize=1, universal_newlines=True, encoding="utf-8")
    for line in p.stdout:
      log.write(line)
      buf.write(line)
    output = buf.getvalue()
    p.wait()
    if p.returncode != 0:
      raise Exception('ffmpeg', src, output)
    if overwrite:
      shutil.move(dest, src)

def ffmpeg_song_duration(path):
  p = subprocess.Popen([ffmpeg(), '-i', path, '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  if p.returncode != 0:
    raise Exception('ffmpeg', p.stdout.decode('utf-8'), p.stderr.decode('utf-8'))
  stderr = err.decode('utf-8')
  for line in stderr.split('\n'):
    #line = str(line)
    if "time=" in line:
      #print(line)
      line = ''.join([char for char in line if char.isdigit() or char.isalpha() or char in [':', '=', ' ']])
      line = line.strip()
      start = line.rfind("time=")
      part2 = line[start:]
      end = part2.find(' ')
      duration_str = part2[len('time='):end]
      duration = datetime.strptime(duration_str, "%H:%M:%S%f")
      #print(duration.hour, duration.minute, duration.second)
      return (duration.hour*60*60) + (duration.minute *60) + duration.second 
  raise Exception('Could not find runtime in ffmped output', stderr) 

def load_music_file(path):
  path = os.path.abspath(path)
  try:
    probe = ffmpeg_probe(path)
    audio_stream = list(filter(lambda x: x["codec_type"] == "audio", probe['streams']))[0]
    duration = float(probe["format"]["duration"])
    size_mb = float(probe["format"]["size"]) / (1024*1024)
    if "bit_rate" in audio_stream:
      bitrate = float(audio_stream['bit_rate'])
    elif "bit_rate" in probe["format"]:
      bitrate = float(probe["format"]['bit_rate']) 
    else:
      raise Exception("Unable to get bitrate from probe!!")
    name = os.path.basename(path)
    num_streams = len(probe['streams'])
    format = os.path.splitext(path)[1]
    if duration > SKIP_DUR_SEC:
      return None
    return name, path, duration, bitrate, size_mb, num_streams, format
  except Exception as e:
    print("ERROR", path, e)
    return None


bad_exts = [".png", ".jpg", ".m3u", ".nfo", ".cue", ".rar", ".log",".txt", ".sfv", ".iso", ".ini", ".jpeg", ""]
def get_files_recurr(folder):
  ret = []
  for item in os.scandir(folder):
    if item.is_dir():
      ret += get_files_recurr(item)
    else:
      name = item.name.lower()
      _, ext = os.path.splitext(name)
      #print(ext)
      if ext in bad_exts:
        continue
      ret.append(os.path.abspath(item.path))
  return ret

def get_files(folders):
  files = []
  for folder in folders:
    folder = os.path.join(MUSIC, folder)
    files += get_files_recurr(folder)
  return files
   
def file_staging_path(src_path):
  path = os.path.join(MUSIC_STAGE_DIR, src_path[len(MUSIC):].strip("/\\"))
  path, _ext = os.path.splitext(path)
  return path + ".mp3"

def shrink_staged_files(playlist_df):
  """
  Shrinks file to be under `SHRINK_SIZE_MB`
  Returns sum of file sizes in MB
  """
  with make_pool() as p:
    return sum(p.starmap(shrink_in_place, playlist_df.iterrows()))

def shrink_in_place(i, pandas_row):
  """
  Shrinks file to be under `SHRINK_SIZE_MB`
  Returns final size in MB
  """
  file_path = file_staging_path(pandas_row.path)
  size_mb = file_size_mb(file_path)
  old_bitrate = ffprobe_bitrate(file_path)
  if pandas_row.duration > 7*60:
    LONG_FILE_BITRATE = 96_000.0
    # don't shrink long files too much, and lose quality
    if size_mb > SHRINK_SIZE_MB or old_bitrate > LONG_FILE_BITRATE:
      write_log(pandas_row["name"], f"fast shrinking: {pandas_row.path}")
      ffmpeg_resize(file_path, file_path, LONG_FILE_BITRATE)
      size_mb = file_size_mb(file_path)
    return size_mb

  new_bitrate = old_bitrate * 0.95
  while size_mb >= SHRINK_SIZE_MB:
    write_log(pandas_row["name"], f"shrinking: {pandas_row.path} {old_bitrate} {new_bitrate}")
    ffmpeg_resize(file_path, file_path, new_bitrate)
    size_mb = file_size_mb(file_path)
    old_bitrate = new_bitrate
    new_bitrate = old_bitrate * 0.90
  return size_mb

def file_to_staging(i, pandas_row):
  def should_format_copy(pandas_row):
    return pandas_row.bitrate > MAX_BITRATE or pandas_row.size_mb >= SHRINK_SIZE_MB or pandas_row.format != ".mp3"
    
  src_file = pandas_row.path
  dest_file = file_staging_path(src_file)
  folders = os.path.dirname(dest_file)
  os.makedirs(folders, exist_ok=True)
  if not os.path.exists(dest_file):
    if should_format_copy(pandas_row):
      write_log(pandas_row["name"], f"shrink copying: {dest_file}")
      ffmpeg_resize(src_file, dest_file, min(pandas_row.bitrate, MAX_BITRATE))
    else:
      name = pandas_row["name"]
      write_log(name, f"copying: {name}")
      shutil.copyfile(src_file, dest_file)

def get_disk_size(df):
  with make_pool() as p:
    return sum(p.map(file_size_mb, df["path"]))

def copy_files(playlist_df):
  with make_pool() as p:
    return p.starmap(file_to_staging, playlist_df.iterrows())
  
movies = ["O Brother, Where Art Thou OST", "Shrek 2 Soundtrack", \
    "Star Wars Revenge of the Sith", "Star Wars The Empire Strikes Back", "The Lord of the Rings The Fellowship of the Ring", \
     "The Lord of the Rings The Return of the King", "TheIncredibles", "Rogue One A Star Wars Story"]
movies = list(map(lambda x: os.path.join("movies", x), movies))

disney = ["Big Hero 6 OST", "Disney Classics 1", "Disney Classics 2", "LiloAndStitch", "Mulan OST", "Tarzan Sountrack", \
    "The Lion King Soundtrack", "Toy Story Trilogy/Toy Story", "Toy Story Trilogy/Toy Story 2"]
disney = list(map(lambda x: os.path.join("movies", x), disney))

games = ["Banjo-Kazooie OST", "Celeste", "Chrono Trigger Orchestral OST", "Finding Paradise OST", "Halo Combat Evolved OST", \
    "Hollow Knight OST", "Jamestown OST", "Legend of Zelda 30th Anniversary Collection", "Mass Effect 2", "Pokemon RSE OST", "To the Moon OST", \
    "Shovel Knight OST", "SNES Mega Man X OST", "Stardew Valley OST", "Materia Collective - An Homage to Game Title Themes"]
games = list(map(lambda x: os.path.join("Games", x), games))

hymns = ["All/7pmChoir", "All/Benedictines", "All/JourneySongs", "All/LaRosa", "All/MartyHaugen", "All/SLJComingHome", "All/SLJOneLordOfAll", "All/SLJSteadfastLove", "NDFC", "SLJMixed"]
hymns = list(map(lambda x: os.path.join("hymns", x), hymns))

bands = ["80s Rock Anthems", "70s Rock Drive", "Boys Like Girls", "Fall Out Boy/2013 - Save Rock And Roll", "Bon Jovi - Greatest Hits", "Creedence Clearwater Revival - Greatest Hits", \
  "Fall Out Boy/American Beauty American Psycho", "Fall Out Boy/Save Rock and Roll", "Lynyrd Skynyrd - Greatest Hits", \
  "Meatloaf - Bat Out Of Hell I and II", "Panic At The Disco\Too Weird To Live, Too Rare To Die!", "Panic At The Disco\Death Of A Bachelor", \
  "AC-DC - Discography/7 Compilations/2004 Greatest Hits 30 Anniversary Edition (2 CD) @320", "Bob Dylan - The Very Best", \
  "John Denver - Greatest Hits", "Journey - Greatest Hits", "Queen Discography/-- Compilations --\(1981) Greatest Hits", \
  "The All-American Rejects - Studio Discography/(2005) The All-American Rejects - Move Along", "The Killers - Direct Hits", \
  "Walk The Moon Talking Is Hard", "VA - Rock Ballads (The Greatest Rock and Power Ballads of the 70s 80s 90s 00s 10s 20s)"]

bands = list(map(lambda x: os.path.join("bands", x), bands))
classic = ["Beethoven", "George Frideric Handel - The Messiah, HWV56 [Pinnock, English Concert] [2CD]", \
  "London Philharmonic Orchestra - The 50 Greatest Pieces Of Classical Music (2011) 16-44 {FLAC} vtwin88cube", "Mozart", \
  "Various Artists - Classical Music Masterpieces (2022) Mp3 320kbps [PMEDIA]", "Debussy - The Best of(1997)", \
  "Dvorak - Symphony No. 9 [Bernstein Century]"]
classic = list(map(lambda x: os.path.join("classic", x), classic))

favs = ["Spotify"]
veggie = ["Veggie Tales Discography 1998-2010 (17 Releases)/Veggie Tales - 2004 - Veggie Rocks", "Veggie Tales Discography 1998-2010 (17 Releases)/Veggie Tales - 2001 - Silly Songs With Larry"]
civil_war = ["Other/Civil War Music Collectors Edition"]

done = [(classic, "Classical"), (civil_war, "Civil War"), (favs, "Favorites"), (movies, "Movie OSTs"), (veggie, "Veggie Tales")]
playlists = [(disney, "Disney"), (games, "Game OSTs"), (hymns, "Hymns"), (bands, "Bands")]

CACHE="music_info.csv"
DATAFRAME_COLS = ["name", "path", "duration", "bitrate", "size_mb", "num_streams", "format"]
def load_data():
  if os.path.exists(CACHE):
    return pd.read_csv(CACHE)
  return pd.DataFrame(columns=DATAFRAME_COLS)

def save_data(df):
  df.to_csv(CACHE, index=False)

def filter_loaded(files, df):
  missing = []
  files_series = pd.Series(files, dtype=str)
  missing = files_series[~files_series.isin(df["path"])]
  return missing.values

def prepare_cache(playlist, cache_df):
  files = get_files(playlist)
  missing = filter_loaded(files, cache_df)
  with make_pool() as p:
    loaded_data = p.map(load_music_file, missing)
    loaded_data = filter(lambda x: x is not None, loaded_data)
    new_df = pd.DataFrame.from_records(loaded_data, columns=DATAFRAME_COLS)
    if len(new_df) > 0:
      if len(cache_df) > 0:
        cache_df = pd.concat([cache_df, new_df])
      else:
        cache_df = new_df
  return cache_df, files

def filter_by_playlist(files, cache_df):
  return cache_df[cache_df["path"].isin(files)]

if __name__ == "__main__":
  clear_logs()
  if os.name == "nt":
    from multiprocessing import freeze_support
    freeze_support()
  total = 0.0
  for playlist, name in playlists:
    print(name, end='')
    df = load_data()
    df, files = prepare_cache(playlist, df)
    playlist_df = filter_by_playlist(files, df)
    save_data(df)
    
    copy_files(playlist_df)
    size_gb = shrink_staged_files(playlist_df) / 1024.0

    two_size_gb = get_disk_size(playlist_df) / 1024.0
    print(f": {size_gb:.2f} GB {two_size_gb:.2f}")
    total += size_gb
    
  total_gb = total
  print(f"{total_gb:.2f} GB")
  