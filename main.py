# Youtube Audio Downloader
import os, re, time, requests, ffmpeg, colorama
from urllib.error import HTTPError, URLError

from moviepy.editor import *
from pytube import *

colorama.init()

total_errors = [0]
titles = []
replace_type = 0


def clear():
    global total_errors, titles
    total_errors = 0
    titles = []
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def downloader(video, vtype):
    global total_errors, titles, replace_type

    print("\033[1;34;40m")

    try:
        # Get video and title
        yt = YouTube(video)
        vidtitle = yt.title
        print("\n" + str(len(titles) + 1) + ". Found Video: " + vidtitle)

        # Get file name
        fname = re.sub(yt.author + " ", "", vidtitle)

        if '-' in re.sub("^(?:\w+\s+){3}([^\n\r]+)$", "", fname) and vtype == 'a':
            fname = re.sub('^[^-]*- ', "", fname)

        fname = re.sub('[\\/:"\'*?<>|.,%#$+!`&{}@=]+', "", fname)

        rep = ' '

        if replace_type == 1:
            fname = re.sub(' ', "_", fname)
            rep = '_'


        fname = re.sub('\([^)]*\)', "", fname)

        if 'ft' in fname:
            fname = re.sub('ft[^|]*', "", fname)

        if fname[-1] == '_':
            fname = fname[:-1]
        if fname[0] == '_':
            fname = fname[0:]

        fname = fname.strip()
        fname = fname.strip('_')

        print('File name will be: ' + fname)

        titles.append(fname)

        if vtype == 'a':
            # Choose Stream
            chosenDownload = yt.streams.get_audio_only()
            print("Located highest bitrate audio stream for video: '" + vidtitle + "'. Downloading now...")

            # Download Vid
            chosenDownload.download(filename=fname + '.mp4', max_retries=5)
            print("Finished Download, converting to mp3 file")

            # Convert from mp4 to mp3
            video = AudioFileClip(fname + '.mp4')

            print("\033[1;31;40m")
            video.write_audiofile(fname + '.mp3')
            print("\033[1;34;40m")

            print("Finished Conversion")

            try:
                os.remove(fname + '.mp4')
            except PermissionError:
                print('MP4 file is being used by another process, retrying delete')
                time.sleep(10)
                os.remove(fname + '.mp4')

            print("Removed mp4")
        elif vtype == 'v':
            # Choose Stream
            chosenDownload = yt.streams.get_highest_resolution()
            print("Located highest resolution video stream for video: '" + vidtitle + "'. Downloading now...")

            # Download Vid
            chosenDownload.download(filename=fname + ".mp4", max_retries=5)
            print("Finished Download")
        elif vtype == 'h':
            fname = fname.strip('-')
            # Choose Stream - video
            chosenDownload = yt.streams.filter(only_video=True).first()
            print("Located highest resolution video stream for video: '" + vidtitle + "'. Downloading now...")
            print('Stream is: ' + str(chosenDownload))

            file_types = {
                'video/webm': '.webm',
                'video/mp4': '.mp4',
            }
            fending = file_types[chosenDownload.mime_type]

            # Download Vid
            chosenDownload.download(filename=fname+'v'+fending, max_retries=5)
            print("Finished Download")


            print("Downloading audio")

            # Choose Stream - audio
            chosenDownload = yt.streams.get_audio_only('webm')
            print("Located highest bitrate audio stream for video: '" + vidtitle + "'. Downloading now...")

            # Download audio
            chosenDownload.download(filename=fname + 'a.webm', max_retries=5)
            print("Finished Download, Combining files")

            input_video = ffmpeg.input(fname + 'v' + fending)
            merged_audio = ffmpeg.input(fname + 'a.webm')

            # Combine Files
            print("\033[1;37;40m")
            time.sleep(2)
            (
                ffmpeg
                .concat(input_video, merged_audio, v=1, a=1)
                .output(fname + ".mp4")
                .run(overwrite_output=True, cmd='ffmpeg.exe')
            )

            # Remove Extras
            os.remove(fname + 'v' + fending)
            os.remove(fname + 'a.webm')

        print("Link to thumbnail: \n" + yt.thumbnail_url)
    except (HTTPError, SyntaxError, OSError) as err:
        print("Error downloading: {}".format(err))
        total_errors[0] += 1
        total_errors.append(video)
    except URLError:
        print("Old connection was forcibly closed, to fix this, restart the program...")
        time.sleep(10)
        quit()

    print("\n")


def downPlaylist(vtype):

    print("\033[1;35;40m")

    playlist = Playlist(input("Link to Playlist: \n"))
    listName = playlist.title
    print("Accessing playlist: " + listName)

    listName = re.sub('[\\/:"\'*?<>|.,%#$+!`&{}@=]+', "", listName)

    try:
        os.mkdir(listName)
    except:
        print("Playlist already downloaded (folder already exists). Carrying on...")

    try:
        url = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['thumbnailRenderer']['playlistCustomThumbnailRenderer']['thumbnail']['thumbnails'][2]['url']
    except KeyError:
        try:
            url = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['thumbnailRenderer']['playlistVideoThumbnailRenderer']['thumbnail']['thumbnails'][2]['url']
        except KeyError:
            print("Cant find playlist thumbnail, are you sure you entered a link to a playlist?")
    print('Thumbnail url is:', url)

    get_thumb = (input("Would you like to download the playlist thumbnail?\n") or 'y')

    try:
        if get_thumb[0].lower() == 'y':
            lname = (listName + '.png')
            data = requests.get(url)
            with open(lname, 'wb')as file:
                file.write(data.content)
            os.rename(lname, listName + "/" + lname)
            print("Downloaded thumbnail")
    except:
        print("Thumbnail already downloaded")

    print("proceeding to download", str(playlist.length) + " files\n")
    for video in playlist:
        downloader(video, vtype)

    global titles, total_errors
    print("\n"*3 + "Finished Downloading. Total errors: ")
    print(total_errors)
    print("Moving to playlist folder now...")

    # Move files
    # Find file ending
    f_end = {
        'a': '.mp3',
        'v': '.mp4',
    }

    mov_errors = []
    for n in titles:
        try:
            os.rename(n + f_end[vtype], listName + "/" + n + ".mp3")
        except:
            print("Error Moving a File")
            mov_errors.append(n)

    print('All moving errors:')
    print(mov_errors)

    print("Finished")


def main():
    global replace_type

    print("\033[1;36;40m")

    # Find if user would like to download 1 file or many files using playlist
    dtype = (input("Would you like to download video's through YouTube playlists? [yes for playlist, no for single video, leave empty for spotify download]\n") or 's')

    replace_type_string = 'n'

    if dtype[0].lower() in ['y','n']:
        vidtype = (input("Would you like to download as a video or audio or high res video? [v or a or h]\n") or 'a')
        replace_type_string = (input('Lastly, would you like to replace spaces in the file name with "_" (underscores)?\n') or 'n')

    if replace_type_string[0].lower() == 'y':
        replace_type = 1

    if dtype[0].lower() == 'y':
        downPlaylist(vidtype[0].lower())
    elif dtype[0].lower() == 'n':
        vidurl = input("Enter link to youtube video\nlink: ")
        downloader(vidurl, vidtype[0].lower())
    else:
        link = input("Link: \n")
        try:
            command = ("spotdl " + link + " --ffmpeg ffmpeg.exe")
            os.system('cmd /c "' + command + '"')
            os.remove('.cache')
        except:
            print("Error getting spotify track")
            print("To use this feature you must have spotify downloader installed:\nhttps://github.com/spotDL/spotify-downloader")
            time.sleep(10)


print("\033[1;32;40m")
print("====================")
print("    By Rohan S.")
print("====================")
main()

x = 1
while x == 1:
    print("\033[1;31;40m")
    exit = (input("Type 'y' to exit, or just click enter to repeat...\n") or '  n')

    if exit[0].lower() == 'y':
        x = 0
    else:
        clear()
        time.sleep(1)
        main()
