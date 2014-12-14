NAME = "ABC"
BASE_URL = "http://abc.go.com"
SHOWS = "http://cdn.abc.go.com/vp2/ws-supt/s/syndication/2000/rss/001/001/-1/-1/-1/-1/-1/-1"
SEASONS = "http://abc.go.com/vp2/s/carousel?service=seasons&parser=VP2_Data_Parser_Seasons&showid=%s&view=season"
EPISODES = "http://abc.go.com/vp2/s/carousel?service=playlists&parser=VP2_Data_Parser_Playlist&postprocess=VP2_Data_Carousel_ProcessPlaylist&showid=%s&seasonid=%s&vidtype=lf&view=showplaylist&playlistid=PL5515994&start=0&size=100&paging=1"

RE_SHOW_ID = Regex('/(SH\d+)')
RE_AIR_DATE = Regex('(?P<month>\d{2})/(?P<day>\d{2})/(?P<year>\d{2})$')

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0'
	HTTP.Headers['X-Requested-With'] = 'XMLHttpRequest'

####################################################################################################
@handler('/video/abc', NAME)
def MainMenu():

	oc = ObjectContainer()

	if not Client.Platform in ('Android', 'iOS', 'Roku') and not (Client.Platform == 'Safari' and Platform.OS == 'MacOSX'):
		oc.header = 'Not supported'
		oc.message = 'This channel is not supported on %s' % (Client.Platform if Client.Platform is not None else 'this client')
		return oc

	for show in XML.ElementFromURL(SHOWS).xpath('//item'):
		title = show.xpath('./title')[0].text.strip()

		# Exclude certain shows
		if title in (
			'ABC News Specials',
			'Boston Med',
			'Good Afternoon America',
			'Nightline Prime: Secrets of Your Mind',
			'Primetime Nightline: Beyond Belief',
			'Primetime: Family Secrets',
			'Rising Up: Five Years Since Katrina',
			'Sandbox'
		): continue

		description = HTML.ElementFromString(show.xpath('./description')[0].text)
		summary = description.xpath('.//p')[0].text

		link = show.xpath('./link')[0].text
		show_id = RE_SHOW_ID.search(link)

		if not show_id:
			continue

		oc.add(DirectoryObject(
			key = Callback(Season, title=title, show_id=show_id.group(1)),
			title = title,
			summary = summary
		))

	return oc

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

		# Just show the most recent season for now. Older videos are not available in the format we want them in.
		break

	return oc

####################################################################################################
@route('/video/abc/episodes')
def Episodes(title, show_id, season):

	oc = ObjectContainer(title2=title)
	html = GetHTML(EPISODES % (show_id, season))

	for episode in html.xpath('//div[contains(@class, "reg_tile")]'):
		url = episode.xpath('./div[@class="tile_title"]/a/@href')[0]
		if not url.startswith('http://'):
			url = BASE_URL + url

		if not '/VDKA' in url and not '/redirect/fep?videoid=VDKA' in url:
			continue

		if '/watch/this-week/' in url:
			url = url.replace('abc.go.com', 'abcnews.go.com')

		title = episode.xpath('./div[@class="tile_title"]/a/text()')[0]
		summary = episode.xpath('./div[@class="tile_desc"]/text()')[0]
		thumb = episode.xpath('./div[@class="thumb"]/a/img/@src')[0]

		try:
			air_date = episode.xpath('./div[@class="show_tile_sub"]/text()')[0]
			date = RE_AIR_DATE.search(air_date).groupdict()
			air_date = '%s-%s-20%s' % (date['month'], date['day'], date['year'])
			originally_available_at = Datetime.ParseDate(air_date).date()
		except:
			originally_available_at = None

		oc.add(VideoClipObject(
			url = '%s#%s' % (url, show_id),
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
