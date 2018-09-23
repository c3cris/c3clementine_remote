import traceback, sys, math
from pprint import pprint
import remotecontrolmessages_pb2 as cr
import pygame as pg
from player import Player
from clemwrapper import ClemWrapper

CAPTION = "c3clementine"
SCREEN_SIZE = (int(1260), int(720))
WIDTH = SCREEN_SIZE[0]
HEIGHT = SCREEN_SIZE[1]


class Control(object):

    def __init__(self):

        self.screen = pg.display.get_surface()
        self.clock = pg.time.Clock()
        self.fps = 30
        self.done = False
        self.viewport = self.screen.get_rect()
        self.room = pg.Surface((4000, 4000)).convert_alpha()
        self.room_rect = self.room.get_rect()
        self.art = pg.Surface((400, 400)).convert_alpha()

        self.playlists = pg.Surface((400, 400)).convert_alpha()
        self.playlists_rect = self.playlists.get_rect(topleft=(50, 400))

        self.songs = pg.Surface((600, 560)).convert_alpha()
        self.songs_rect = self.songs.get_rect(topleft=(550, 100))
        self.songs_rect.width=585

        self.pg = pg
        self.p = Player(self.pg, self)
        self.keys = self.pg.key.get_pressed()

        self.songs.fill(color=(255, 255, 255, 0))
        self.playlists.fill(color=(255, 255, 255, 0))

        self.connection = ClemWrapper(self.p, "192.168.1.165", 5500, 1234,
                                      False, True, 21)

    def display_fps(self):
        caption = "{} - fps: {:.2f}".format(CAPTION, self.clock.get_fps())
        self.pg.display.set_caption(caption)

    def draw(self):

        self.room.fill(color=(255, 255, 255, 0))
        self.screen.fill(color=(255, 255, 255))

        if self.p.update_art and self.p.art is not None:
            self.art.fill(color=(255, 255, 255, 0))
            self.art.blit(self.p.art, (0, 0))
            self.update_art = False

        self.screen.blit(self.pg.transform.smoothscale(self.art, (200, 200)), (290, 100))

        if self.p.songs_change:
            self.songs.fill(color=(255, 255, 255, 0))

        if self.p.playlist_change:
            self.playlists.fill(color=(255, 255, 255, 0))


        self.p.draw(self.room)
        self.screen.blit(self.songs, self.songs_rect)
        self.screen.blit(self.playlists, self.playlists_rect)

        self.screen.blit(self.room, (0, 0), self.viewport)

    def draw_text(self, msg, x, y, size=18, color="blue"):
        # ['arial', 'arialblack', 'bahnschrift', 'calibri', 'cambriacambriamath', 'cambria', 'candara',
        # 'comicsansms', 'consolas', 'constantia', 'corbel', 'couriernew', 'ebrima', 'franklingothicmedium',
        # 'gabriola', 'gadugi', 'georgia', 'impact', 'inkfree', 'javanesetext', 'leelawadeeui',
        # 'leelawadeeuisemilight', 'lucidaconsole', 'lucidasans', 'malgungothic', 'malgungothicsemilight',
        # 'microsofthimalaya', 'microsoftjhengheimicrosoftjhengheiui', 'microsoftjhengheimicrosoftjhengheiuibold',
        # 'microsoftjhengheimicrosoftjhengheiuilight', 'microsoftnewtailue', 'microsoftphagspa',
        # 'microsoftsansserif', 'microsofttaile', 'microsoftyaheimicrosoftyaheiui',
        # 'microsoftyaheimicrosoftyaheiuibold', 'microsoftyaheimicrosoftyaheiuilight', 'microsoftyibaiti',
        # 'mingliuextbpmingliuextbmingliuhkscsextb', 'mongolianbaiti', 'msgothicmsuigothicmspgothic', 'mvboli',
        # 'myanmartext', 'nirmalaui', 'nirmalauisemilight', 'palatinolinotype', 'segoemdl2assets', 'segoeprint',
        # 'segoescript', 'segoeui', 'segoeuiblack', 'segoeuiemoji', 'segoeuihistoric', 'segoeuisemibold',
        # 'segoeuisemilight', 'segoeuisymbol', 'simsunnsimsun', 'simsunextb',
        font_type = pg.font.match_font("consolas")
        font = pg.font.Font(font_type, size)
        text = font.render(str(msg), True, self.pg.Color(color))
        rect = text.get_rect(topleft=(x, y))
        return text, rect

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.done = True
                self.connection.connected = False
                self.connection.thread.join()
                self.connection.soc.close()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    msg = cr.Message()
                    msg.type = cr.SET_VOLUME
                    msg.request_set_volume.volume = int(self.p.volume - 10)
                    self.send_message(msg)

                elif event.key == pg.K_RIGHT:
                    msg = cr.Message()
                    msg.type = cr.SET_VOLUME
                    msg.request_set_volume.volume = int(self.p.volume + 10)
                    self.send_message(msg)

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = self.pg.mouse.get_pos()
                    if self.p.volume_rect.collidepoint((x, y)):
                        self.p.updating_volume = True
                    if self.p.position_rect.collidepoint((x, y)):
                        self.p.updating_position = True
                    if self.p.scroll.collidepoint((x, y)):
                        self.p.updating_scroll = True

            elif event.type == pg.MOUSEBUTTONUP:
                x, y = self.pg.mouse.get_pos()

                if event.button == 1:
                    if self.p.updating_volume:
                        self.p.updating_volume = False
                        msg = cr.Message()
                        msg.type = cr.SET_VOLUME
                        msg.request_set_volume.volume = self.p.volume
                        self.connection.send_message(msg)
                    if self.p.updating_scroll:
                        self.p.updating_scroll = False
                    if self.p.updating_position:
                        self.p.updating_position = False
                        msg = cr.Message()
                        msg.type = cr.SET_TRACK_POSITION
                        msg.request_set_track_position.position = self.p.position
                        self.connection.send_message(msg)

                    if self.p.prev.collidepoint((x, y)):
                        msg = cr.Message()
                        msg.type = cr.PREVIOUS
                        self.connection.send_message(msg)
                    elif self.p.next.collidepoint((x, y)):
                        msg = cr.Message()
                        msg.type = cr.NEXT
                        self.connection.send_message(msg)
                    elif self.p.pause_play.collidepoint((x, y)):
                        msg = cr.Message()
                        msg.type = cr.PLAYPAUSE
                        self.connection.send_message(msg)

                    if self.songs_rect.collidepoint((x, y)):
                        if self.p.active_playlist:
                            msg = cr.Message()
                            msg.type = cr.CHANGE_SONG

                            song_o_index = int(math.floor(min(y - 10 - self.songs_rect.y, 25 * 22) / 22)
                                               + self.p.song_start)
                            if song_o_index <  len(self.p.songs[self.p.active_playlist]):
                                song = self.p.songs[self.p.active_playlist][song_o_index]
                                msg.request_change_song.playlist_id = self.p.active_playlist
                                msg.request_change_song.song_index = song["index"]
                                self.connection.send_message(msg)
                                self.songs_change = True

                    if self.playlists_rect.collidepoint((x, y)):
                        msg = cr.Message()
                        msg.type = cr.REQUEST_PLAYLIST_SONGS

                        playlist_index = int(
                            min(len(self.p.playlists),
                                max(0, math.floor(y - 10 - self.playlists_rect.y - self.p.playlists_rect.y) / 22)))

                        playlist_id = self.p.playlists_order[playlist_index]

                        msg.request_playlist_songs.id = playlist_id

                        self.connection.send_message(msg)
                        self.playlists_change = True

                if self.playlists_rect.collidepoint((x, y)):
                    if event.button == 4:

                        self.p.playlists_rect.move_ip(0, 30)
                        self.p.playlist_change = True
                    elif event.button == 5:
                        # down
                        self.p.playlists_rect.move_ip(0, -30)
                        self.p.playlist_change = True

                if self.songs_rect.collidepoint((x, y)):
                    if event.button == 4:

                        self.p.song_start -= 5
                        self.p.songs_change = True
                    elif event.button == 5:
                        # down
                        self.p.song_start += 5
                        self.p.songs_change = True

            if event.type == pg.USEREVENT:
                self.pg.time.set_timer(self.pg.USEREVENT, 0)

    def update(self):
        self.keys = pg.key.get_pressed()
        self.p.update()

    def main_loop(self):
        self.pg.time.set_timer(self.pg.USEREVENT, 2000)

        while not self.done:
            try:
                self.event_loop()
                self.update()
                self.draw()
                pg.display.update()
                if self.p.playlist_change_b == self.p.playlist_change:
                    self.p.playlist_change = False
                if self.p.songs_change_b == self.p.songs_change:
                    self.p.songs_change = False
                if self.p.active_playlist == self.p.new_active_pl:
                    self.p.new_active_pl = False

                self.clock.tick(self.fps)
                self.display_fps()
            except Exception as e:
                pprint(e)
                print(traceback.format_exc())
                print("error occured closing gracefully")
                self.done = True
                self.connection.connected = False
                self.connection.thread.join()
                self.connection.soc.close()


if __name__ == "__main__":
    pg.init()
    pg.display.set_caption(CAPTION)
    pg.display.set_mode(SCREEN_SIZE)
    run = Control()
    run.main_loop()
    pg.quit()
    sys.exit()
