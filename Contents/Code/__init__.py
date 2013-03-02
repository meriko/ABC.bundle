NAME = "ABC"
SHOWS = "http://cdn.abc.go.com/vp2/ws-supt/s/syndication/2000/rss/001/001/-1/-1/-1/-1/-1/-1"
SEASONS = "http://abc.go.com/vp2/s/carousel?service=seasons&parser=VP2_Data_Parser_Seasons&showid=%s&view=season"
EPISODES = "http://abc.go.com/vp2/s/carousel?service=playlists&parser=VP2_Data_Parser_Playlist&postprocess=VP2_Data_Carousel_ProcessPlaylist&showid=%s&seasonid=%s&vidtype=lf&view=showplaylist&playlistid=PL5515994&start=0&size=100&paging=1"

VIDEO_INFO = "http://cdn.abc.go.com/vp2/ws/s/contents/2000/utils/mov/13/9024/%s/432"
RE_SHOW_ID = Regex('/(SH[0-9]+)')

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0'

####################################################################################################
@handler('/video/abc', NAME)
def MainMenu():

	oc = ObjectContainer()

	for show in XML.ElementFromURL(SHOWS, cacheTime=CACHE_1DAY).xpath('//item'):
		title = show.xpath('./title')[0].text

		description = HTML.ElementFromString(show.xpath('./description')[0].text)
		summary = description.xpath('.//p')[0].text
		thumb = description.xpath('.//img')[0].get('src')

		link = show.xpath('./link')[0].text
		showId = RE_SHOW_ID.search(link).group(1)

		oc.add(DirectoryObject(
			key = Callback(Season, title=title, showId=showId),
			title = title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(url=thumb)
		))

	return oc

####################################################################################################
@route('/video/abc/season')
def Season(title, showId):

	oc = ObjectContainer(title2=title)

	for season in HTML.ElementFromURL(SEASONS % showId, cacheTime=CACHE_1DAY).xpath('//a'):
		title = season.text
		seasonid = season.get('seasonid')

		if not seasonid:
			seasonid = title.rsplit(' ', 1)[1]

		oc.add(DirectoryObject(
			key = Callback(Episodes, title=title, showId=showId, season=seasonid),
			title = title
		))

	return oc

####################################################################################################
@route('/video/abc/episodes')
def Episodes(title, showId, season):

	oc = ObjectContainer(title2=title)

	for episode in HTML.ElementFromURL(EPISODES % (showId, season)).xpath('//div[@class="tile"]'):
		url = episode.xpath('./div[@class="tile_title"]/a')[0].get('href')
		title = episode.xpath('./div[@class="tile_title"]/a')[0].text
		summary = episode.xpath('./div[@class="tile_desc"]')[0].text
		thumb = episode.xpath('./div[@class="thumb"]/a/img')[0].get('src')

		try:
			date = episode.xpath('./div[@class="show_tile_sub"]')[0].text.rsplit(' ', 1)[1]
			originally_available_at = Datetime.ParseDate(date).date()
		except:
			originally_available_at = None

		oc.add(VideoClipObject(
			url = url,
			title = title,
			summary = summary,
			thumb = thumb = Resource.ContentsOfURLWithFallback(url=thumb)
		))

	return oc
