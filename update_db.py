#!/usr/bin/python

import os
import sys
import time
import sqlite3
import requests
import xml.etree.ElementTree as ET

#RSS_LINK = 'http://freezone.iinet.net.au/rss/freezone-radio.rss'
#RSS_LINK_RAW = 'http://freezone.iinet.net.au/rss/freezone-radio-raw.rss'
RSS_LINK = 'http://freezone.iinet.net.au/freezone-radio-playlist.rss'
BANSHEE_DB_FILE = os.path.join(os.environ['HOME'], '.config/banshee-1/banshee.db')
XML_NS = {'content': 'http://purl.org/rss/1.0/modules/content/'}  # XML Namespace
BANSHEE_NEW_RADIO_TUPLE = (5, 1, 1, 1, 0, 0, None, None, None, 0, 0, 0, 0, 5, 0, None, None, None, None, 0, 0, 0, 0, 0,
                           0, 'Radio', None, None, None, None, None, None, 0, 0, 0, 0, None, None, 0, 0, None, 0, 0, 0)

# Banshee DB "PrimarySourceID"s
#
class BansheeSources:
    MUSIC = 1
    RADIO = 5
    PODCASTS = 6

class IINetStation:
    # http://freezone.iinet.net.au/freezone-radio-playlist.rss
    #
    #   <item>
    #       <title>SomaFM: The Trip</title>
    #       <link>http://radio1.internode.on.net:8000/284</link>
    #       <bitrate>128</bitrate>
    #       <badlang>0</badlang>
    #       <description>
    #           From SomaFM.com: Progressive house / trance. Tip top tunes.
    #       </description>
    #   </item>

    def __init__(self, xml_item):
        self.title = xml_item.find('title').text
        self.link = xml_item.find('link').text
        self.bitrate = xml_item.find('bitrate').text
        self.desc = xml_item.find('description').text.strip()
        self.genre = None

    # Has no stream link, but has the genre
    # http://freezone.iinet.net.au/rss/freezone-radio.rss
    #
    #  <item>
    #    <title><![CDATA[SomaFM: The Trip]]></title>
    #    <link>http://freezone.iinet.net.au/radio/fz-radio/house/591</link>
    #    <guid isPermaLink="false">591</guid>
    #    <description><![CDATA[<img src="http://asse" width="224" height="126" />
    #      From SomaFM.com: Progressive house / trance. Tip top tunes.]]>
    #    </description>
    #    <content:encoded><![CDATA[Fom SomaFM.com: Pr]]></content:encoded>
    #    <pubDate>Thu, 01 Jan 1970 00:00:00 +0000</pubDate>
    #    <thumb url="http://" width="224" height="126"/>
    #    <category>House</category>
    #  <item>

    def set_genre(self, xml_item):
        if xml_item.find('category') is not None:
            self.genre = xml_item.find('category').text

    def __str__(self):
        return 'Station: %s "%s"' % (self.title, self.desc)

class BansheeTrack:

    def __init__(self, track_row=BANSHEE_NEW_RADIO_TUPLE):
        self.track_row = track_row

        self.source = track_row[0]              # 5 = Radio
        self.id = track_row[1]                  # Unique
        self.artistid = track_row[2]            # ??
        self.url = track_row[7]
        self.title = track_row[15]              # 'Soma FM: The Trip'
        self.titlelowered = track_row[16]       # 'soma fm the trip'
        self.genre = track_row[25]              # "Progressive", "Dance", etc
        self.comment = track_row[31]            # 'From SomaFM.com: Progressive house / trance. Tip top tunes.'
        self.dateadded = track_row[38]          # epoch
        self.dateupdated = track_row[39]
        self.lastsyncedstamp = track_row[42]

    # Returns a string that can be used in a SQL INSERT statement
    def rowstr(self):
        row = list(BANSHEE_NEW_RADIO_TUPLE)
        row[0] = self.source
        row[1] = self.id
        row[2] = self.artistid
        row[7] = self.url
        row[15] = self.title
        row[16] = self.titlelowered
        row[25] = self.genre
        row[31] = self.comment
        row[38] = self.dateadded
        row[39] = self.dateupdated
        row[42] = self.lastsyncedstamp

        # Python 'None' should be NULL fields in SQLite
        for i in range(0, len(row)):
            if row[i] is None:
                row[i] = '**FIELD*IS*NULL**'

        result = str(tuple(row)).replace("'**FIELD*IS*NULL**'", 'NULL')

        return result

        '''
        ('PrimarySourceID', 'TrackID', 'ArtistID', 'AlbumID', 'TagSetID', 'ExternalID', 'MusicBrainzID',
         'Uri', 'MimeType', 'FileSize', 'BitRate', 'SampleRate', 'BitsPerSample', 'Attributes',
         'LastStreamError', 'Title', 'TitleLowered', 'TitleSort', 'TitleSortKey', 'TrackNumber',
         'TrackCount', 'Disc', 'DiscCount', 'Duration', 'Year', 'Genre', 'Composer', 'Conductor', 'Grouping',
         'Copyright', 'LicenseUri', 'Comment', 'Rating', 'Score', 'PlayCount', 'SkipCount', 'LastPlayedStamp',
         'LastSkippedStamp', 'DateAddedStamp', 'DateUpdatedStamp', 'MetadataHash', 'BPM', 'LastSyncedStamp',
         'FileModifiedStamp')

(5, 1,   1, 1, 0, 0, None, u'http://freezone.iin', None, 0, 0, 0, 0, 5, 0, u'Soma FM: The Trip', u'soma fm the trip', None, rw, size 39 at 0xb6c6af50>, 0, 0, 0, 0, 0, 0,
  u'Progressive', None, None, None, None, None, u'From SomaFM.com: Progressive house / trance. Tip top tunes.', 0, 0, 0, 0, None, None, 1458769239, 1459913792,
  u'da839bc005faee1b578ac40b31e63108', 0, 1458769239, 0)
(1, 18,  5, 3, 0, 0, None, u'file:///home/tim/De', u'taglib/mp3', 1910912, 252, 44100, 0, 5, 0, u'Tool 3', u'tool 3', None, rw, size 17 at 0xb6beebb8>, 7, 0, 0, 0, 60526, 2003,
  u'Dance', u'Umek', None, None, None, None, None, 0, 100, 1, 0, 1459898474, None, 1459897155, 1459897155, u'bc0fe98d6b31cd730561411cee3e1476', 0, 1459897155, 1426872664)
(6, 19, 16, 4, 0, 1, None, u'http://mpegmedia.ab', u'video/mp4', 109967844, 0, 0, 0, 21, 0, u'Good Game Episode 08, 2016', u'good game episode 08 2016', None, <rea, size 57 at 0xb6bd0aa0>,
0, 0, 0, 0, 1800000, 2016, u'Podcast', None, None, None, None, None, None, 0, 0, 0, 0, None, None, 1460015661, 1460015661, u'77c5bd530114228b919de3d087d5a6ec', 0, 1460015661, 0)
        '''

class BansheeDB:
    def __init__(self, file=BANSHEE_DB_FILE):
        self.file = file
        self.tracks = {}
        self._highest_track_id = 0

        self.conn = sqlite3.connect(BANSHEE_DB_FILE)
        self.cursor = self.conn.cursor()
        self._read_tracks()

    def _list_tables(self):

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for table in self.cursor.fetchall():
            print table[0]

    def _read_tracks(self, print_column_names=False):
        self.tracks = {}
        self.cursor.execute("SELECT * FROM CoreTracks;")
        for row in self.cursor.fetchall():
            id = row[1]
            title = row[15]

            self.tracks[title.lower()] = BansheeTrack(row)

            if id > self._highest_track_id:
                self._highest_track_id = id

        if print_column_names:
            columns = [ d[0] for d in self.cursor.description ]
            print columns

    def list_tracks(self):
        for title,track in self.tracks.items():
            print title, track.url

    def get_track(self, title):
        return self.tracks.get(title)

    def update_details(self, title, new_title, new_url, new_genre, new_comment):
        track = self.get_track(title)
        updated = False
        if new_title != track.title:
            print "%s: Updating TITLE %s -> %s" % (title, track.title, new_title)
            self.cursor.execute("UPDATE CoreTracks SET Title = '%s' WHERE TrackID = %d;" % (new_title, track.id))
            self.cursor.execute("UPDATE CoreTracks SET TitleLowered = '%s' WHERE TrackID = %d;" % (new_title.lower(), track.id))
            updated = True
        if new_url != track.url:
            print "%s: Updating URL %s -> %s" % (title, track.url, new_url)
            self.cursor.execute("UPDATE CoreTracks SET Uri = '%s' WHERE TrackID = %d;" % (new_url, track.id))
            updated = True
        if new_genre != track.genre:
            print "%s: Updating Genre %s -> %s" % (title, track.genre, new_genre)
            self.cursor.execute("UPDATE CoreTracks SET Genre = '%s' WHERE TrackID = %d;" % (new_genre, track.id))
            updated = True
        if new_comment != track.comment:
            print "%s: Updating Comment %s -> %s" % (title, track.comment, new_comment)
            self.cursor.execute("UPDATE CoreTracks SET Comment = '%s' WHERE TrackID = %d;" % (new_comment, track.id))
            updated = True

        if not updated:
            print "NO CHANGE."

    def close(self):
        self.conn.commit()
        self.conn.close()

    def add_track(self, track):
        print "%s: Adding -> %s" % (track.title, track.comment)
        cmd = "INSERT INTO CoreTracks VALUES %s ;" % track.rowstr()
        self.cursor.execute(cmd)
        self._highest_track_id = track.id

    def track_exists(self, title):
        return title in self.tracks

    def next_track_id(self):
        return self._highest_track_id + 1


db = BansheeDB()
#db._list_tables()
db.list_tracks()

#r = requests.get(RSS_LINK)
#radio_xml = r.text
#tree = ET.parse('./freezone-radio.rss')
tree = ET.parse('./freezone-radio-playlist.rss')
root = tree.getroot()

stations = {}

for item in root.find('channel').findall('item'):
    #title = item.find('title').text
    station = IINetStation(item)
    station_name = station.title.lower()

    if db.track_exists(station_name):
        db.update_details(station_name, station.title, station.link, station.genre, station.desc)
    else:
        epoch_now = int(time.time())
        dbtrack = BansheeTrack()
        dbtrack.source = BansheeSources.RADIO
        dbtrack.id = db.next_track_id()
        dbtrack.url = station.link
        dbtrack.title = station.title
        dbtrack.titleLowered = station.title.lower()
        dbtrack.genre = station.genre
        dbtrack.comment = station.desc
        dbtrack.dateadded = epoch_now
        dbtrack.dateupdated = epoch_now
        dbtrack.lastsyncedstamp = epoch_now

        db.add_track(dbtrack)


db.close()

