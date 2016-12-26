import os
import logging
from socket import error as SocketError
from time import sleep
import pygame
import image_tools

__author__ = 'jeroen'


paths = {}
# values for keys 'music_path' and 'playlists_path' are initialized in concrete MyMPD constructors


class Playlist:

    def __init__(self, pl_dict, img_loader, def_img):
        self.playlist = pl_dict['playlist']
        self.last_modified = pl_dict['last-modified']
        self.cover_img = def_img

        self.listeners = []

        m3u_file = self.playlist + '.m3u'
        with open(os.path.join(paths['playlists_path'], m3u_file), 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for l in lines:
                if l.startswith('#path='):
                    self.path = l.split('=')[1].lstrip('./')
                elif l.startswith('#cover='):
                    self.cover = l.split('=')[1]
                if hasattr(self, 'path') and hasattr(self, 'cover'):
                    break  # exit lines-loop
        try:
            img_loader.add_work(os.path.join(paths['music_path'] + self.path, self.cover), self.set_cover)
        except AttributeError:
            pass

    def set_cover(self, cover):
        self.cover_img = cover
        for l in self.listeners:
            l.playlist_updated()

    def add_listener(self, listener):
        self.listeners.append(listener)

    def __str__(self):
        return "Playlist{'" + self.playlist + "', last_modified: '" + self.last_modified + "', path: '" + self.path\
               + "', cover: '" + self.cover + "', cover_img: '" + str(self.cover_img) + "'}"


class MyMPD:
    def __init__(self):
        self.loader = image_tools.Loader()
        self.default_cover = None
        self.loader.add_work(filename=os.path.join('player_icons', 'unknown.png'), callback=self.__set_def_img)
        self.loader.join()
        logging.debug("MyMPD init finished, self.default_cover=" + str(self.default_cover))

    def __set_def_img(self, img):
        self.default_cover = img

    def connect(self):
        raise NotImplementedError

    def init_playlists(self):
        raise NotImplementedError

    # Methods to be propagated to real MPDClient

    def clear(self):
        raise NotImplementedError

    def previous(self):
        raise NotImplementedError

    def next(self):
        raise NotImplementedError

    def play(self):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def setvol(self, v):
        raise NotImplementedError

    def load(self, playlist):
        raise NotImplementedError

    def status(self):
        """
        :return dictionary with these keys:
            'volume'
            'song' --> 0-based index of current song in playlist, key not present if not playing
            'nextsong' --> key should not be present if there is no next song
            'elapsed' --> time passed (in seconds)
        """
        raise NotImplementedError

    def currentsong(self):
        """
        :return dictionary with these keys:
            'time' --> total time (in seconds), key should not be present if not currently playing
        """
        raise NotImplementedError


class WinMPD(MyMPD):

    volume = 80
    current_playlist = None
    current_song = None
    current_time = None
    elapsed = None

    song_duration = 60  # fake same length for all songs
    song_count = 10  # fake a length of 10 songs for all playlists

    playing = False
    paused = None

    def __init__(self):
        MyMPD.__init__(self)

        global paths
        base_path = "\\\\DiskStation\\"
        paths['music_path'] = base_path + 'music\\'
        paths['playlists_path'] = "\\\\DiskStation\\home\\linuxconfig\\playlists\\"

        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self):
        pass

    def init_playlists(self):
        playlists = []

        listdir = os.listdir(paths['playlists_path'])
        listdir.sort()

        for f in listdir: #[:13]:  # load only 13 playlists
            if f.endswith('.m3u'):
                playlist = Playlist({'playlist':f[:-4],'last-modified':'now'}, self.loader, self.default_cover)
                playlists.append(playlist)
                self.logger.debug("loaded playlist " + str(playlist.playlist))
            else:
                self.logger.debug("no playlist: " + str(f))

        self.logger.info("%d playlists loaded", len(playlists))

        return playlists

    def clear(self):
        self.logger.debug("clear")
        self.playing = False
        self.current_playlist = None
        self.current_song = None
        self.current_time = None

    def pause(self):
        self.logger.debug("pause")
        self.paused = True

    def stop(self):
        self.logger.debug("stop")
        self.playing = False

    def previous(self):
        self.logger.debug("previous")
        if not self.current_playlist:
            raise SystemError("no playlist!?")
        self.go_to(self.current_song - 1)

    def next(self):
        self.logger.debug("next")
        if not self.current_playlist:
            raise SystemError("no playlist!?")
        self.go_to(self.current_song + 1)

    def go_to(self, song):
        self.logger.debug("go_to " + str(song))
        if song < 1 or song > 10:
            raise SystemError("song " + str(song))
        import time
        self.current_song = song
        self.elapsed = 0
        self.current_time = time.time()

    def setvol(self, v):
        self.logger.debug("setvol " + str(v))
        self.volume = v

    def play(self):
        self.logger.debug("play")
        if not self.playing:
            import time
            if self.current_song is None:
                self.go_to(1)
            else:
                self.go_to(self.current_song)
            self.playing = True
        elif self.paused:
            self.paused = False

    def load(self, playlist):
        self.logger.debug("load playlist " + str(playlist))
        self.current_playlist = playlist

    def currentsong(self):
        if self.current_song:
            return {'time':self.song_duration}
        return {}

    def status(self):
        status = {'volume':self.volume}
        if self.current_song:
            if self.elapsed > self.song_duration:
                if self.current_song < self.song_count:
                    self.go_to(self.current_song + 1)
                else:
                    self.current_song = None
                    self.stop()

            status['song']=str(self.current_song-1)  # -1 want zero-based
            status['track']=self.current_song
            status['title']='Liedje nummer ' + str(self.current_song)
            if self.playing:
                import time
                now = time.time()
                if not self.paused:
                    delta = now - self.current_time
                    self.elapsed = self.elapsed + delta
                self.current_time = now
                status['elapsed'] = int(self.elapsed)
            if self.current_song < self.song_count:
                status['nextsong']=self.current_song  # niet +1 want zero-based
        return status


class PiMPD(MyMPD):
    connected = False

    def __init__(self):
        MyMPD.__init__(self)

        import mpd

        global paths
        mpd_path = "/var/lib/mpd/"
        paths['music_path'] = mpd_path + "music/"
        paths['playlists_path'] = mpd_path + "playlists/"

        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = mpd.MPDClient()
        self.client.timeout = 10

    def connect(self):
        while not self.connected:
            try:
                self.client.connect('localhost', 6600)
                self.connected = True
            except SocketError as e:
                self.logger.error(str(e))

            if not self.connected:
                self.logger.debug("mpd: Couldn't connect. Retrying...")
                sleep(5)

        self.logger.debug("mpd: connected, status=" + self.client.status()['state'])

    def init_playlists(self):
        if not self.connected:
            self.connect()
        playlists = []
        source = self.client.listplaylists()
        source.sort(key=lambda current: current['playlist'])

        for pl in source:
            playlist = Playlist(pl, self.loader, self.default_cover)
            playlists.append(playlist)
            self.logger.debug("loaded playlist " + str(playlist.playlist))

        self.logger.info("%d playlists loaded", len(playlists))

        return playlists

    def clear(self):
        self.client.clear()

    def previous(self):
        self.client.previous()

    def next(self):
        self.client.next()

    def play(self):
        self.client.play()

    def pause(self):
        self.client.pause()

    def stop(self):
        self.client.stop()

    def setvol(self, v):
        self.client.setvol(v)

    def load(self, playlist):
        self.client.load(playlist)

    def currentsong(self):
        return self.client.currentsong()

    def status(self):
        # client.status()
        # {'songid': '1', 'playlistlength': '15', 'playlist': '18', 'repeat': '0', 'consume': '0', 'mixrampdb': '0.000000', 'random': '0', 'state': 'play', 'xfade': '0', 'volume': '55', 'single': '0', 'mixrampdelay': 'nan', 'nextsong': '1', 'time': '70:172', 'song': '0', 'elapsed': '69.590', 'bitrate': '1155', 'nextsongid': '2', 'audio': '44100:16:2'}
        # client.currentsong()
        # {'album': 'Sensacional', 'albumartistsort': 'Tattoo del Tigre, El', 'date': '2003', 'title': 'El Tattoo del Tigre', 'track': '1', 'artist': 'El Tattoo del Tigre', 'albumartist': 'El Tattoo del Tigre', 'pos': '0', 'musicbrainz_albumid': '5e97a895-e962-4f1e-ac24-bdf7727d47a1', 'last-modified': '2013-01-29T21:08:26Z', 'disc': '1', 'musicbrainz_albumartistid': '328f63af-ccf1-4735-b493-c5490281e5ca', 'artistsort': 'Tattoo del Tigre, El', 'file': 'library/El Tattoo Del Tigre/[2003] Sensacional/01 El Tattoo Del Tigre - El Tattoo Del Tigre.flac', 'time': '173', 'genre': 'Pop', 'musicbrainz_artistid': '328f63af-ccf1-4735-b493-c5490281e5ca', 'musicbrainz_trackid': '87e82228-d36d-44b8-8f6b-894b32ddadc8', 'id': '1'}
        copy = self.client.status().copy()
        copy.update(self.client.currentsong())
        return copy
