#!/usr/bin/python

import os
import sys
import sqlite3
import requests
import xml.etree.ElementTree as ET

RSS_LINK = 'http://freezone.iinet.net.au/rss/freezone-radio.rss'
RSS_LINK_RAW = 'http://freezone.iinet.net.au/rss/freezone-radio-raw.rss'
BANSHEE_DB = os.path.join(os.environ['HOME'], '.config/banshee-1/banshee.db')
NS = {'content': 'http://purl.org/rss/1.0/modules/content/'}  # XML Namespace

# "PrimarySourceID"s
class Sources:
    MUSIC = 1
    RADIO = 5
    PODCASTS = 6

class Station:
    def __init__(self, xml_item):
        self.title = xml_item.find('title').text
        self.guid = xml_item.find('guid').text
        self.link = xml_item.find('link').text
        self.rawlink = None
        self.desc = xml_item.find('content:encoded', NS).text
        self.thumbnail = None
        if xml_item.find('thumb') is not None:
            self.thumbnail = xml_item.find('thumb').get('url', default='')

    def __str__(self):
        return 'Station: %s "%s"' % (self.title, self.desc)


#r = requests.get(RSS_LINK)
#radio_xml = r.text

tree = ET.parse('/tmp/freezone-radio.rss')
root = tree.getroot()

stations = {}
for item in root.find('channel').findall('item'):
    title = item.find('title').text
    stations[title] = Station(item)

conn = sqlite3.connect(BANSHEE_DB)
c = conn.cursor()

#c.execute("SELECT name FROM sqlite_master WHERE type='table';")
#for i in c.fetchall():
'''
[(u'CoreConfiguration',), (u'CorePrimarySources',), (u'CoreTracks',), (u'CoreAlbums',), (u'CoreArtists',),
 (u'CorePlaylists',), (u'CorePlaylistEntries',), (u'CoreSmartPlaylists',), (u'CoreSmartPlaylistEntries',),
 (u'CoreRemovedTracks',), (u'CoreCacheModels',), (u'CoreShuffles',), (u'CoreShufflers',), (u'CoreShuffleModifications',),
 (u'sqlite_stat1',), (u'CoverArtDownloads',), (u'LastfmStations',), (u'IaItems',), (u'HyenaModelVersions',),
 (u'PodcastSyndications',), (u'PodcastItems',), (u'PodcastEnclosures',), (u'Bookmarks',)]
'''

c.execute("select * from CoreTracks;")
for track in c.fetchall():
    if track[0] == Sources.RADIO:
        print track

print
columns = [ d[0] for d in c.description ]
print 'Column Names are:', columns

