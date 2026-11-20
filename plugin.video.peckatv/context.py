"""Context menu in the Kodi TV guide (IPTV Simple channels): record the selected programme on Pecka.TV."""
import calendar
import re
import time
from urllib.parse import urlencode

import xbmc

PLUGIN = 'plugin://plugin.video.peckatv/'


def _order(fmt):
    """Order of day/month/year in a regional date format ('%d.%m.%Y', 'DD/MM/YYYY', ...)."""
    f = fmt.lower()
    pos = {k: f.find(k) for k in ('d', 'm', 'y')}
    return sorted(pos, key=lambda k: pos[k] if pos[k] >= 0 else 99)


def parse_start(date_str, time_str, date_fmt):
    """Local unix timestamp from Kodi's localized ListItem.StartDate + ListItem.StartTime, or None."""
    d = re.findall(r'\d+', date_str or '')
    t = re.findall(r'\d+', time_str or '')
    if len(d) < 3 or len(t) < 2:
        return None
    parts = dict(zip(_order(date_fmt or '%d.%m.%Y'), (int(x) for x in d[:3])))
    year = parts.get('y', 0)
    if year < 100:
        year += 2000
    hour, minute = int(t[0]), int(t[1])
    ts = (time_str or '').lower()
    if 'pm' in ts and hour < 12:
        hour += 12
    elif 'am' in ts and hour == 12:
        hour = 0
    try:
        return int(time.mktime((year, parts['m'], parts['d'], hour, minute, 0, 0, 0, -1)))
    except (KeyError, ValueError, OverflowError):
        return None


def start_from_path(path):
    """EPG items carry their UTC start in the path: pvr://guide/0147/2026-11-20 21:10:00.epg"""
    m = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\.epg', path or '')
    return calendar.timegm(tuple(int(x) for x in m.groups()) + (0, 0, 0)) if m else None


def start_from_date(date_label, date_fmt):
    """Fallback: ListItem.Date = '<dateshort> HH:MM' (e.g. '20.11.2026 22:10')."""
    parts = (date_label or '').rsplit(' ', 1)
    return parse_start(parts[0], parts[1], date_fmt) if len(parts) == 2 else None


def main():
    info = {k: xbmc.getInfoLabel('ListItem.%s' % k)
            for k in ('ChannelName', 'FileNameAndPath', 'Date', 'StartTime', 'Title', 'EpgEventTitle')}
    date_fmt = xbmc.getRegion('dateshort')
    start = start_from_path(info['FileNameAndPath']) or start_from_date(info['Date'], date_fmt)
    xbmc.log('[plugin.video.peckatv] guide context %s, dateshort=%r -> start=%s' % (info, date_fmt, start),
             xbmc.LOGINFO)
    params = {'action': 'guide_record', 'channel': info['ChannelName'],
              'title': info['EpgEventTitle'] or info['Title']}
    if start:
        params['start'] = start
    xbmc.executebuiltin('RunPlugin(%s?%s)' % (PLUGIN, urlencode(params)))


if __name__ == '__main__':
    main()
