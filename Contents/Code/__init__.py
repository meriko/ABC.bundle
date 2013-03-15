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
	HTTP.Headers['X-Requested-With'] = 'XMLHttpRequest'

####################################################################################################
@handler('/video/abc', NAME)
def MainMenu():

	oc = ObjectContainer()

	if not Client.Platform in ('iOS', 'Roku') and not (Client.Platform == 'Safari' and Platform.OS == 'MacOSX'):
		if Client.Platform in ('Android') or Client.Product in ('Web Client'):
			oc.add(Error('This channel isn\'t supported on %s' % Client.Platform))
		oc.header = 'Not supported'
		oc.message = 'This channel isn\'t supported on %s' % Client.Platform
		return oc

	for show in XML.ElementFromURL(SHOWS).xpath('//item'):
		title = show.xpath('./title')[0].text.strip()

		description = HTML.ElementFromString(show.xpath('./description')[0].text)
		summary = description.xpath('.//p')[0].text
		thumb = description.xpath('.//img')[0].get('src')

		link = show.xpath('./link')[0].text
		show_id = RE_SHOW_ID.search(link)

		if not show_id:
			continue

		oc.add(DirectoryObject(
			key = Callback(Season, title=title, show_id=show_id.group(1)),
			title = title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(url=thumb)
		))

	return oc

####################################################################################################
@route('/video/abc/error')
def Error(title):

	return DirectoryObject(
		key = Callback(Error, title=title),
		title = title
	)

####################################################################################################
@route('/video/abc/season')
def Season(title, show_id):

	oc = ObjectContainer(title2=title)
	html = GetHTML(SEASONS % show_id)

	for season in html.xpath('//a'):
		title = season.text
		season_id = season.get('seasonid')

		if not season_id:
			season_id = title.rsplit(' ', 1)[1]

		oc.add(DirectoryObject(
			key = Callback(Episodes, title=title, show_id=show_id, season=season_id),
			title = title
		))

	return oc

####################################################################################################
@route('/video/abc/episodes')
def Episodes(title, show_id, season):

	oc = ObjectContainer(title2=title)
	html = GetHTML(EPISODES % (show_id, season))

	for episode in html.xpath('//div[@class="tile"]'):
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
			thumb = Resource.ContentsOfURLWithFallback(url=thumb)
		))

	return oc

####################################################################################################
def GetHTML(url):

	try:
		html = HTML.ElementFromURL(url, sleep=5.0)
	except:
		html = HTML.ElementFromURL(url, cacheTime=0)

	return html
