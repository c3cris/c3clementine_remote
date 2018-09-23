import math
from io import BytesIO

class Player(object):

    def __init__(self, pg, control):
        self.position = 0
        self.volume = 0
        self.track = None
        self.songs = {}
        self.playlists = None
        self.playlists_order = None
        self.shuffle = 0
        self.song_start = 0
        self.clem_update = False
        self.state = ""
        self.pg = pg
        self.control = control
        self.updating_volume = False
        self.updating_position = False
        self.x_offset = 50
        self.volume_rect = pg.Rect((self.x_offset, 250), (8, 8))
        self.volume_rect.center = (self.x_offset, 250)
        self.position_rect = pg.Rect((self.x_offset, 250), (8, 8))
        self.position_rect.center = (self.x_offset, 300)
        self.prev = pg.Rect((self.x_offset, 320), (60, 25))
        self.next = pg.Rect((self.x_offset + 150, 320), (60, 25))
        self.pause_play = pg.Rect((self.x_offset + 70, 320), (60, 25))
        self.play_status = "PLAY"
        self.playlists_rect = pg.Rect((0, 0), (400, 400))
        self.songs_rect = pg.Rect((0, 0), (500, 600))
        self.active_playlist = 0
        self.update_art = False
        self.art = None
        self.new_active_pl = False
        self.playlist_change = False
        self.songs_change = False
        self.playlist_change_b = self.playlist_change
        self.songs_change_b = self.songs_change

    def update(self):

        if self.new_active_pl:
            self.active_playlist = self.new_active_pl
            self.songs_change = True
            self.playlist_change = True

        self.playlist_change_b = self.playlist_change
        self.songs_change_b = self.songs_change

        if self.updating_volume:
            x, y = self.pg.mouse.get_pos()
            new_x = max(self.x_offset, min(self.x_offset + 200, x))
            if new_x != self.volume_rect.x:
                new_volume = int(((float(new_x) - self.x_offset) / 200) * 100)
                self.control.connection.set_volume(new_volume)

                self.volume = new_volume
                self.volume_rect.x = int(new_x)

        if self.updating_position:
            x, y = self.pg.mouse.get_pos()
            new_x = max(self.x_offset, min(self.x_offset + 200, x))
            if new_x != self.position_rect.x:
                new_position = int(((float(new_x) - self.x_offset) / 200) * self.track.length)
                self.position = new_position
                self.position_rect.x = int(new_x)

    def draw(self, surf):

        y = 30
        if self.track is not None:
            surf.blit(*self.control.draw_text("Track: " + str(self.track.title), self.x_offset, y))
            y += 20
            surf.blit(*self.control.draw_text("Artist: " + str(self.track.artist), self.x_offset, y))
            y += 20
            surf.blit(*self.control.draw_text("Album: " + str(self.track.album), self.x_offset, y))

            surf.blit(*self.control.draw_text("Volume: " + str(self.volume), self.x_offset, 220))

            surf.blit(*self.control.draw_text("Position: " +
                                              self.get_formatted_position(self.position) + " / " +
                                              self.track.pretty_length, self.x_offset, 270))
            surf.blit(*self.control.draw_text("State: " + str(self.state), self.x_offset, 140))

            surf.blit(*self.control.draw_text("PREV", self.prev.x, self.prev.y, 25))
            surf.blit(*self.control.draw_text(self.play_status, self.pause_play.x, self.prev.y, 25))
            surf.blit(*self.control.draw_text("NEXT", self.next.x, self.next.y, 25))

            surf.blit(*self.control.draw_text("Playlists: ", 50, 370))
            surf.blit(*self.control.draw_text("Songs: ", 550, 120))

        if self.playlists is not None and self.playlist_change:
            self.draw_playlists(self.control.playlists)

        if self.active_playlist in self.songs and self.songs_change:
            self.draw_songs(self.control.songs)

        self.draw_position(surf)
        self.draw_volume(surf)
        self.draw_art()

    def draw_position(self, surf):

        if self.track is not None and self.track.index != 0:
            self.pg.draw.line(surf, self.pg.Color("green"), (self.x_offset, 300), (self.x_offset + 200, 300), 3)
            pos = float(self.position) / float(self.track.length)
            self.position_rect.x = int(pos * 200) + self.x_offset
            self.pg.draw.circle(surf, self.pg.Color("black"), self.position_rect.center, 5)

    def draw_volume(self, surf):

        self.pg.draw.line(surf, self.pg.Color("green"), (self.x_offset, 250), (self.x_offset + 200, 250), 3)
        pos = float(self.volume) / 100
        self.volume_rect.x = pos * 200 + self.x_offset
        self.pg.draw.circle(surf, self.pg.Color("black"), self.volume_rect.center, 5)

    def draw_playlists(self, surf):

        y = 10 + self.playlists_rect.y

        for playlist in self.playlists:

            if self.playlists[playlist]["closed"]:
                color = "lightgray"
            else:
                color = "black"
            if self.playlists[playlist]["active"]:
                color = "green"

            surf.blit(*self.control.draw_text(str(self.playlists[playlist]["name"]) +
                                              "  [" + str(self.playlists[playlist]["item_count"]) + "]", 15, y, 20,
                                              color))
            y += 22

    def draw_songs(self, surf):
        y = 10
        cur_playlist_id = self.active_playlist

        if self.song_start < 0:
            self.song_start = 0
        elif self.song_start + 25 > self.playlists[cur_playlist_id]["item_count"]:
            self.song_start = self.playlists[cur_playlist_id]["item_count"] - 25

        for i in range(self.song_start, self.song_start + 25):

            color = "black"

            if i < len(self.songs[cur_playlist_id]) and self.songs[cur_playlist_id][i]["id"] == self.track.id:
                color = "green"

            surf.blit(*self.control.draw_text(
                str(self.songs[cur_playlist_id][i]["title"][0:30]) +
                "  [" + str(self.songs[cur_playlist_id][i]["artist"]) + "]", 15, y, 20, color))
            y += 22

        self.pg.draw.line(surf, self.pg.Color("gray"), (595, 0), (595, 550), 3)
        pos = float(self.song_start) / float(self.playlists[cur_playlist_id]["item_count"] - 25)
        new_y = int(pos * 550 + 5)
        self.pg.draw.circle(surf, self.pg.Color("black"), (595, new_y), 5)

    def get_formatted_position(self, pos):
        pos = float(pos)
        hour = minute = second = 0
        hour = int(math.floor(pos / 3600))
        minute = int((pos / 60)) % 60
        second = int(pos % 60)
        return "{h}:{m}:{s}".format(s=second, m=minute, h=hour)

    def draw_art(self):
        if self.update_art and self.track.art != "":
            img = BytesIO(self.track.art)
            self.art = self.pg.image.load(img)
