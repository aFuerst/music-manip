import eyed3
import os
import os.path

path = "C:\\Users\\Alex\\Music\\Games"
album = "Legend of Zelda The Twilight Princess OST"

# update metadata
if(os.path.isdir(os.path.join(path, album))):
	i = 1
	print(os.path.join(path, album))
	for item in os.listdir(os.path.join(path, album)):
		if(os.path.isdir(os.path.join(path, album, item))):
			for file in os.listdir(os.path.join(path, album, item)):
				#print(file)
				if("mp3" in file):
					#print(os.path.join(path, album, item, file))
					#audiofile = eyed3.load(os.path.join(path, album, item, file))
					#audiofile.tag = eyed3.id3.Tag()
					#audiofile.tag.artist = u"Bioware"
					#audiofile.tag.album = album
					#audiofile.tag.track_num = i
					#audiofile.tag.title = file
					#audiofile.tag.album_artist = u"Bioware"
					#audiofile.tag.save()
					i += 1

# rename files
garbage = "The Legend of Zelda - The Twilight Princess OST - "
if(os.path.isdir(os.path.join(path, album))):
	i = 1
	print(os.path.join(path, album))
	for item in os.listdir(os.path.join(path, album)):
		if(os.path.isdir(os.path.join(path, album, item))):
			for file in os.listdir(os.path.join(path, album, item)):
				if("mp3" in file):
					pass
					#audiofile = eyed3.load(os.path.join(path, file))
					#newName = os.path.join(path, audiofile.tag.title + ".mp3")
					#sp = file.find(' ') + 1
					newName = os.path.join(path, album, file[len(garbage):])
					#newName = os.path.join(path,file[:-len(garbage)] + ".mp3")
					print(newName)
					os.rename(os.path.join(path, album, item, file), newName)
