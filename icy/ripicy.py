#!/usr/bin/env python

"""
Copyright (c) 2006 Matin Tamizi

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Based on:
SHOUTcast Stream Ripper by espitech
http://www.codeproject.com/cs/media/SHOUTcastRipper.asp

"Shoutcast Metadata Protocol"
http://www.smackfu.com/stuff/programming/shoutcast.html
"""

import binascii, os, re, sys, urllib2


class datablock:
    data = ''
    size = 0


"""
Connects to the shoutcast stream and requests metadata in the stream
"""
def connect(url):
    request = urllib2.Request(url)
    request.add_header('Icy-MetaData', '1')
    opener = urllib2.build_opener()

    return opener.open(request)


"""
Parses the header based on <key>:<value>
"""
def parse_html_header(fd):
    header = {}
    eof = False

    while not eof:
        s = fd.readline()
        s = s.rstrip('\r\n')

        if len(s) is 0:
            eof = True
            pass
        else:
            colon_loc = s.find(':')
            if colon_loc >= 0:
                header[s[:colon_loc]] = s[colon_loc+1:]

    return header

"""
metadata -- holds metadata bytes and length
mp3data -- hold mp3 block bytes and length
curr_title -- most recent StreamTitle sent in metadata
prev_title -- second most recent StreamTitle sent in metadata
song -- file descriptor for the current song
title_format -- regular expression to match StreamTitle in metadata
"""        
def main():
    metadata = datablock()
    mp3data = datablock()
    curr_title = None
    prev_title = None
    song = None
    title_format = re.compile(r'StreamTitle=\'(.+?)\';')

    try:
        url = sys.argv[1]
    except:
        print >> sys.stderr, 'USAGE:', sys.argv[0], 'url'
        return 1
        
    stream = connect(url)
    header = parse_html_header(stream)
    mp3data.size = int(header['icy-metaint'])

    try:
        while True:
            mp3data.data = stream.read(mp3data.size)
        
            metadata.size = int( binascii.hexlify(stream.read(1)), 16 ) * 16
            metadata.data = stream.read(metadata.size)

            title = title_format.match(metadata.data)

            if title:
                if curr_title != title.group(1):
                    print >> sys.stderr, '\nSong change has occurred'
                    prev_title = curr_title
                    curr_title = title.group(1)
                    
                    if prev_title == None:
                        print >> sys.stderr, 'Waiting for second song...'
                        continue
                    else:
                        print >> sys.stderr, 'Writing song \"%s\" ...' % curr_title
                        song = open(curr_title + '.mp3', 'w')

            try:
                sys.stderr.write('.')
                song.write(mp3data.data)
            except AttributeError:
                # have not opened file for writing
                pass
                    
    except KeyboardInterrupt:
        print >> sys.stderr, '\nRip interrupted'
        try:
            os.remove(song.name)
            print >> sys.stderr, 'Removing partial song \"%s\" ...' % curr_title
        except OSError:
            print >> sys.stderr, 'No songs written'
        
if __name__ == '__main__':
    main()
