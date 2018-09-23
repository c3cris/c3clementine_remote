import socket, struct, traceback
from threading import Thread
import clementine_pb2 as cr
from io import BytesIO
from pprint import pprint

class ClemWrapper(object):
  def __init__(self, p, ip, port, auth_code, download, send_list, version):
    self.ip = ip
    self.port = port
    self.auth_code = auth_code
    self.download = download
    self.send_list = send_list
    self.version = version
    self.p = p
    self.connected = False
    self.soc = None

    self.connect()
    self.thread = Thread(None,self.client_thread, "Client Thread")
    self.thread.daemon = True
    self.thread.start()

  def connect(self):
    self.soc = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
    self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    self.soc.connect((self.ip, self.port))

    msg_c = cr.Message()
    msg_c.type = cr.CONNECT
    msg_c.request_connect.auth_code = self.auth_code
    msg_c.request_connect.downloader = self.download
    msg_c.request_connect.send_playlist_songs = self.send_list
    self.connected = True
    sent = self.send_message(msg_c)

  def send_message(self, msg):
    if self.soc is not None:
      msg.version = self.version
      ser = msg.SerializeToString()
      data = struct.pack(">I", len(ser)) + ser
      self.soc.send(data)

  def client_thread(self):

    try:
      while self.soc is not None and self.connected:
        data = bytes()
        first = self.soc.recv(4)
        first_unpacked = struct.unpack(">I", first)
        (msg_len, ) = first_unpacked
        # pprint(first_unpacked)
        bytes_recv = 0

        if not msg_len: continue
        while msg_len > bytes_recv:
          temp = self.soc.recv(min(4096, msg_len - bytes_recv))
          data += temp
          bytes_recv += len(temp)
          # pprint((msg_len, bytes_recv, len(temp), min(4096, msg_len - bytes_recv)))
          
        # print(msg_len, len(data))

        # exit()
        msg = cr.Message()
        msg.ParseFromString(data)
        self.parse_response(msg)
    except Exception as e:
        print("Child Thread error occured closing gracefully")
        print(traceback.format_exc())
        raise e


  def parse_response(self, msg):

    if msg.type == cr.INFO:
      # self.version = msg.response_clementine_info.version
      self.state = cr.EngineState.Name(msg.response_clementine_info.state)
      print("INFO - ver:{version}, state: {state}".format(version = self.version
        , state = self.state))
      self.p.state = self.state

      if self.state == "PAUSE":
        self.p.play_status = "PLAY"
      elif self.state == "Playing":
        self.p.play_status = "PAUSE"
    
    elif msg.type == cr.CURRENT_METAINFO:
      print("got new metainfo")
      current = msg.response_current_metadata.song_metadata
      self.p.track = current
      self.p.update_art = True
      self.p.songs_change = True

      # print("id: " + unicode(current.id) + "\n" +
      #       "index: " + unicode(current.index) + "\n" +
      #       "title: " + unicode(current.title) + "\n" +
      #       "album: " + unicode(current.album) + "\n" +
      #       "artist: " + unicode(current.artist) + "\n" +
      #       "albumartist: " + unicode(current.albumartist) + "\n" +
      #       "track: " + unicode(current.track) + "\n" +
      #       "disc: " + unicode(current.disc) + "\n" +
      #       "pretty_year: " + unicode(current.pretty_year) + "\n" +
      #       "genre: " + unicode(current.genre) + "\n" +
      #       "playcount: " + unicode(current.playcount) + "\n" +
      #       "pretty_length: " + unicode(current.pretty_length) + "\n" +
      #       "length: " + unicode(current.length) + "\n" +
      #       "is_local: " + unicode(current.is_local) + "\n" +
      #       "filename: " + unicode(current.filename) + "\n" +
      #       "file_size: " + unicode(current.file_size) + "\n" +
      #       "rating: " + unicode(current.rating) + "\n" +
      #       "url: " + unicode(current.url) + "\n" +
      #       "art_automatic: " + unicode(current.art_automatic) + "\n" +
      #       "art_manual: " + unicode(current.art_manual) + "\n" +
      #       "type: " + unicode(current.type) + "\n")
    
    elif msg.type == cr.FIRST_DATA_SENT_COMPLETE:
      pprint("first data sent comeplete")
    
    elif msg.type == cr.KEEP_ALIVE:
      pprint("keep alive")
    
    elif msg.type == cr.SET_VOLUME:
      pprint("Volume " + unicode(msg.request_set_volume.volume))
      if not self.p.updating_volume:
        self.p.volume = msg.request_set_volume.volume
    
    elif msg.type == cr.UPDATE_TRACK_POSITION:
      if not self.p.updating_position:
        self.p.position = msg.response_update_track_position.position
        # pprint(self.p.position)
    
    elif msg.type == cr.SHUFFLE:
      pprint("Suffle " + unicode(msg.shuffle.shuffle_mode))
      self.p.shuffle = msg.shuffle.shuffle_mode

    elif msg.type == cr.ACTIVE_PLAYLIST_CHANGED:
      print("Playlist")
      if not self.p.active_playlist:
        self.p.playlists[self.p.active_playlist]["active"] = False
        
      self.p.active_playlist = msg.response_active_changed.id
      self.p.playlists[self.p.active_playlist]["active"] = True
      self.p.playlist_change = True
      self.p.songs_change = True


    elif msg.type == cr.PLAYLIST_SONGS:
      pprint("got songs")
      songs = []

      for current in msg.response_playlist_songs.songs:
        song = {
          "id" :current.id,
          "index" :current.index,
          "title" :current.title,
          "album" :current.album,
          "artist" :current.artist,
          "albumartist" :current.albumartist,
          "track" :current.track,
          "disc" :current.disc,
          "pretty_year" :current.pretty_year,
          "genre" :current.genre,
          "playcount" :current.playcount,
          "pretty_length" :current.pretty_length,
          "length" :current.length,
          "is_local" :current.is_local,
          "filename" :current.filename,
          "file_size" :current.file_size,
          "rating" :current.rating,
          "url" :current.url,
          "art_automatic" :current.art_automatic,
          "art_manual" :current.art_manual,
          "type" :current.type
        }
        songs.append(song)
      
      self.p.songs[msg.response_playlist_songs.requested_playlist.id] = songs

      print(self.p.active_playlist)

      if self.p.active_playlist:
        self.p.playlists[self.p.active_playlist]["active"] = False

      self.p.new_active_pl = msg.response_playlist_songs.requested_playlist.id
      self.p.playlists[self.p.new_active_pl]["active"] = True
      self.p.songs_change = True
      self.p.playlist_change = True

    elif msg.type == cr.PLAYLISTS:
      print("GOT PLAYLISTS")
      # pprint("playlists " + str(msg.response_playlists.playlist))
      playlists = {}
      playlists_order = []
      for playlist in msg.response_playlists.playlist:

        plist = {
          "id" : playlist.id,
          "name" : playlist.name,
          "item_count" : playlist.item_count,
          "active" : playlist.active,
          "closed" : playlist.closed,
        }

        playlists[plist["id"]] = plist
        playlists_order.append(plist["id"])

        if plist["active"]:
          self.p.new_active_pl = plist["id"]

      self.p.playlists = playlists
      self.p.playlists_order = playlists_order
      self.p.playlist_change = True

    elif msg.type == cr.PAUSE:
      self.p.play_status = "PLAY"
    elif msg.type == cr.PLAY:
      self.p.play_status = "PAUSE"
    else:
      pprint(msg)