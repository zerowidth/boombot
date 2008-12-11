
from supybot.commands import *
import supybot.callbacks as callbacks
# from BeautifulSoupJK import BeautifulSoup
from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import re


class Outside(callbacks.Plugin):
    """Some useful tools for Outside."""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def _getsoup(self,loc,sel):
        baseurl = "http://mobile.weather.gov/"
        firsturl = baseurl + "port_zc.php?inputstring=%s" % urllib.quote(loc)
        try:
            page = urllib.urlopen(firsturl).read()
            soup = BeautifulSoup(page)
            secondurl = baseurl + soup.find('a')['href'] + '&select=%d'%sel
            page = urllib.urlopen(secondurl).read()
            soup = BeautifulSoup(page)
            return soup
        except IOError:
            self.err(irc,"error retreiving info about outside.  Are you sure it's still there?")
            return False

    def forecast(self, irc, msg, args, loc):
        """[location]
            location can be either zip or city, state
            (sorry, you international folks have to go look out a window)
            tells you the forecast for your area
        """
        soup = self._getsoup(loc,1)  # 1 is forecast
        forecasts = soup.findAll('b')
        ret = loc + ' - '
        for i in range(2,5):
            ret += forecasts[i].next.upper() + forecasts[i].nextSibling + ' '
        irc.reply(ret)
    forecast = wrap(forecast, ['text'])

   
    def weather(self, irc, msg, args, loc):
        """[location]
            location can be either zip or city, state  
            (sorry, you international folks have to go look out a window)
            tells you the current weather for your area"""
        soup = self._getsoup(loc,3)  # 3 is current conditions
        loc = soup.div.contents[2].strip()
        gps = soup.div.contents[8].strip().replace('&nbsp;','')
        cur = soup.div.contents[12].strip().replace('&deg;','')
        tmp = soup.div.contents[14].strip().replace('&deg;','').replace(' ','')
        hum = soup.div.contents[16].strip().replace(' ','')
        wnd = soup.div.contents[18].strip().replace(' ','')
        irc.reply(" - ".join( (loc,tmp,cur,hum,wnd,gps)))
    weather = wrap(weather, ['text'])

    def errout(self,irc,msg):
        irc.reply(msg)
        return
        

Class = Outside

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78: