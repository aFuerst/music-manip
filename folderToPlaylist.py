import os
import os.path
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import urllib.parse

class MusicFile:
	def __init__(self, entry, containingFolder):
		self._path = entry.path
		self._folder = containingFolder

	def xml(self):
		pass

	def __str__(self):
		if (self._path.split(".")[-1].lower() == "pdf"):
			print(self._path)
		pt = os.path.join("..", self._path).replace("\\", "/")
		return "file:///" + urllib.parse.quote(pt)

def add_file(xml, file: MusicFile, cnt: int):
	track = ET.SubElement(xml, "track")
	loc = ET.SubElement(track, "location").text = str(file)
	ext = ET.SubElement(track, "extension", attrib={
	                          "application": "http://www.videolan.org/vlc/playlist/0"})
	# <vlc:id>0</vlc:id>
	vlc = ET.SubElement(ext, "vlc:id").text = str(cnt)

def get_files(folder):
	ret = []
	for item in os.scandir(folder):
		if item.is_dir():
			ret += get_files(item)
		else:
			name = item.name.lower()
			if not ("png" in name or "jpg" in name):
				ret.append(MusicFile(item, folder))
	return ret

MUSIC_LOC = "E:/Music"
def create_playlist(folders: list[str], outfile: str):
	files = []

	for folder in folders:
		files += get_files(os.path.join(MUSIC_LOC, folder))

	root = ET.Element("playlist", attrib={"xmlns":"http://xspf.org/ns/0/", "xmlns:vlc":"http://www.videolan.org/vlc/playlist/ns/0/", "version":"1"})
	ET.SubElement(root, "title").text = "Playlist"
	tracklist = ET.SubElement(root, "trackList")
	extension = ET.SubElement(root, "extension", attrib={"application":"http://www.videolan.org/vlc/playlist/0"})
	cnt = 0

	for item in files:
		add_file(tracklist, item, cnt)
		cnt += 1

	for i in range(cnt):
		vlc = ET.SubElement(extension, "vlc:item", attrib={"tid":str(i)})

	with open(os.path.join(MUSIC_LOC, "playlists", f"{outfile}.xspf"), mode="w") as f:
		sting = ET.tostring(root, 'unicode')
		f.write(minidom.parseString(sting).toprettyxml(indent=" "))

create_playlist(["Christmas"], "Christmas")
create_playlist(["bands", "classic", "Games", "hymns", "Movies", "Other", "Vanessa_Mae_Coreography", "Veggie Tales Discography 1998-2010 (17 Releases)"], "all")
create_playlist(["bands"], "bands")
create_playlist(["Other/Civil War Music Collectors Edition"], "civil_war")
create_playlist(["classic"], "classic")
create_playlist(["bands/Fall Out Boy"], "FoB")
create_playlist(["games"], "games")
create_playlist(["bands/Fall Out Boy", "bands/My Chemical Romance - Discography", "bands/Panic At The Disco", "bands/Boys Like Girls"], "anternative")
create_playlist(["Movies"], "movies")
create_playlist(["bands/Panic At The Disco"], "panic")
create_playlist(["bands/My Chemical Romance - Discography"], "MCR")
create_playlist(["Veggie Tales Discography 1998-2010 (17 Releases)"], "VeggieTales")
create_playlist(["Movies/Solo A Star Wars Story", "Movies/Star Wars The Return of the Jedi", "Movies/Star Wars The Phantom Menace", "Movies/Star Wars The Last Jedi", "Movies/Star Wars The Force Awakens", "Movies/Star Wars The Empire Strikes Back", "Movies/Star Wars Revenge of the Sith", "Movies/Star Wars Extras", "Movies/Star Wars Attack of the Clones", "Movies/Star Wars A New Hope"], "SW")
create_playlist(["Games/Legend of Zelda The Wind Waker OST", "Games/Legend of Zelda The Twilight Princess OST", "Games/Legend of Zelda The Orchestral Journey", "Games/Legend of Zelda Skyward Sword OST", "Games/Legend of Zelda Ocarina of Time Soundtrack", "Games/Legend of Zelda MissingLink", "Games/Legend of Zelda LinksAwakening OST", "Games/Legend of Zelda Concert 2018", "Games/Legend of Zelda Breath of the Wild OST", "Games/Legend of Zelda 30th Anniversary Collection", "Games/Legend of Zelda 25th OST", "Games/LoZMissingLink","Games/Rozen"], "zelda")
create_playlist(["Games/Rozen"], "rozen")
create_playlist(["Games/Pokemon RSE OST", "Games/Pokemon RBY OST", "Games/Pokemon GSC OST", "Games/Pokemon BW OST", "Games/Pokemon Best", "Games/Pocket Monsters OST Best 1997-2010"], "pokemon")
create_playlist(["hymns/",], "hymns")
create_playlist(["Christmas/Advent/", "hymns/Advent"], "advent")
create_playlist(["hymns/Lent"], "Lent")
