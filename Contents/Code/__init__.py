import re

NAME = "ABC"
ART = "art-default.jpg"
ICON = "icon-default.png"

SHOWS = "http://cdn.abc.go.com/vp2/ws-supt/s/syndication/2000/rss/001/001/-1/-1/-1/-1/-1/-1"
SEASONS = "http://abc.go.com/vp2/s/carousel?service=seasons&parser=VP2_Data_Parser_Seasons&showid=%s&view=season"
EPISODES = "http://abc.go.com/vp2/s/carousel?service=playlists&parser=VP2_Data_Parser_Playlist&postprocess=VP2_Data_Carousel_ProcessPlaylist&showid=%s&seasonid=%s&vidtype=lf&view=showplaylist&playlistid=PL5515994&start=0&size=100&paging=1"

VIDEO_INFO = "http://cdn.abc.go.com/vp2/ws/s/contents/2000/utils/mov/13/9024/%s/432"

####################################################################################################
def Start():

	Plugin.AddPrefixHandler("/video/abc", MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	MediaContainer.viewGroup = "InfoList"

	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:10.0.2) Gecko/20100101 Firefox/10.0.2"

####################################################################################################
def MainMenu():

	dir = MediaContainer()

	for show in XML.ElementFromURL(SHOWS, cacheTime=CACHE_1DAY).xpath('//item'):
		title = show.xpath('./title')[0].text

		description = HTML.ElementFromString(show.xpath('./description')[0].text)
		summary = description.xpath('.//p')[0].text
		thumb = description.xpath('.//img')[0].get('src')

		link = show.xpath('./link')[0].text
		showId = re.search('/(SH[0-9]+)', link).group(1)

		dir.Append(Function(DirectoryItem(Season, title=title, summary=summary, thumb=Function(GetThumb, url=thumb)), showId=showId))

	return dir

####################################################################################################
def Season(sender, showId):

	dir = MediaContainer(title2=sender.itemTitle)

	for season in HTML.ElementFromURL(SEASONS % showId, cacheTime=CACHE_1DAY).xpath('//a'):
		title = season.text
		season = title.rsplit(' ', 1)[1]

		dir.Append(Function(DirectoryItem(Episodes, title=title, season=season), showId=showId, season=season))

	return dir

####################################################################################################
def Episodes(sender, showId, season):

	dir = MediaContainer(title2=sender.itemTitle)

	for episode in HTML.ElementFromURL(EPISODES % (showId, season)).xpath('//div[@class="tile"]'):
		title = episode.xpath('./div[@class="tile_title"]/a')[0].text
		summary = episode.xpath('./div[@class="tile_desc"]')[0].text
		thumb = episode.xpath('./div[@class="thumb"]/a/img')[0].get('src')

		try:
			sub = episode.xpath('./div[@class="show_tile_sub"]')[0].text
			date = sub.rsplit(' ', 1)[1]
			date = Datetime.ParseDate(date).date()
			subtitle = 'Air date: ' + date.strftime('%a, %B %d %Y')
		except:
			subtitle = ''

		link = episode.xpath('./div[@class="tile_title"]/a')[0].get('href')
		episodeId = re.search('/(VD[0-9]+)', link).group(1)

		dir.Append(Function(VideoItem(PlayVideo, title=title, summary='\n\n'.join([summary, subtitle]), thumb=Function(GetThumb, url=thumb)), episodeId=episodeId))

	return dir

####################################################################################################
def PlayVideo(sender, episodeId):

	info = XML.ElementFromURL(VIDEO_INFO % episodeId)
	streamer = 'rtmp://abcondemandfs.fplive.net/abcondemand/'
	clip = info.xpath('//videos/video[@bitrate="1000"]')[0].get('src')

	return Redirect(RTMPVideoItem(streamer, clip))

####################################################################################################
def GetThumb(url):

	try:
		data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))
