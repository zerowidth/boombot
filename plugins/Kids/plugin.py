
import calculator
reload(calculator)
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sys,time,random,string
from webutil.BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import re


class Kids(callbacks.Plugin):
    """Some useful tools for Kids."""
    tips = 0

    _allchars = string.maketrans('','')

    def _prepare_term(self,s,keep=""):
        #return self._makefilter(string.letters+keep)(s).capitalize()
        return self._makefilter(string.letters+string.digits+keep)(s)

    def _makefilter(self,keep):
        _delchars = self._allchars.translate(self._allchars,keep)
        return lambda s,a=self._allchars,d=_delchars: s.translate(a,d)

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def define(self,irc,msg,args):
        """[word]
        look up the word in wordnet"""
        if len(args) != 1:
            irc.reply("you gotta give me a word to define")
            return
        word = self._prepare_term(args[0],"")
        url = 'http://wordnet.princeton.edu/perl/webwn?s=' + word
        html = urllib2.urlopen(url).read()
        soup = BeautifulSoup()
        soup.feed(html)
        maintable = soup.fetch('li')
        retdef = []
        checkfordefs = len(maintable)
        if checkfordefs != 0:
            for lines in maintable:
                converttostring = str(lines)
                definition = re.sub('^.*\(|\).*$', '', converttostring)
                retdef.append(definition)
        else:
            retdef.append("not found.  Is %s spelled corectly?" % word)
        irc.reply(word + ": " + "; ".join(retdef))

    def calc(self,irc,msg,args):
        """
        >>>(405 - 396) * 3
        (405-396)*3 = 27.0
        """
        s = " ".join(args).strip().replace(' ','')
        val = calculator.parse_and_calc(s)
        result = "%s = %s"%(s, val.__str__(), )
        irc.reply(result)

    def _is_cve_number(self,cve):
        """
        >>> _is_cve_number('CVE-2009-1234') and True
        True
        >>> _is_cve_number('can-2009-1234') and True
        True
        >>> _is_cve_number('2009-1234') and True
        True
        """
        cve_re = re.compile(r'^(?:(?:can|cve)?\-?)\d{4}\-\d+$',re.IGNORECASE)
        return cve_re.match(cve)

    def _cve(self,cve):
        """
        return url and description for a cve entry
        """
        url = 'http://cve.mitre.org/cgi-bin/cvename.cgi?name=' + cve
        html = urllib2.urlopen(url).read()
        soup = BeautifulSoup(html)
        err = soup.find('h2').contents[0]
        if re.search(r'ERROR', err):
            return "No data found regarding " + cve
        div = soup.find('div',id='GeneratedTable')
        if not div or not div.table:
            return "Parse error searching for " + cve
        desc = div.table.findAll('tr')[3].td.contents[0]
        desc = ' '.join(desc.split())
        ret = "%s %s" % (url, desc)
        return ret.strip()

    def cve(self,irc,msg,args):
        word= self._prepare_term(args[0],"-")
        if self._is_cve_number(word):
            irc.reply(self._cve(word))
        else:
            irc.reply("Not a CVE number: " + word)

Class = Kids


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
