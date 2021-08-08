import base64
import calendar
import math
import os
import re
import time
import warnings
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from six.moves import urllib

import interSubs_config as config
from data_provider.pons import pons_combos


def listen(word, type='gtts'):
    if type == 'pons':
        if config.lang_from + config.lang_to in pons_combos:
            url = 'http://en.pons.com/translate?q=%s&l=%s%s&in=%s' % (
                quote(word), config.lang_from, config.lang_to, config.lang_from)
        else:
            url = 'http://en.pons.com/translate?q=%s&l=%s%s&in=%s' % (
                quote(word), config.lang_to, config.lang_from, config.lang_from)

        p = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'}).text
        x = re.findall('<dl id="([a-zA-Z0-9]*?)" class="dl-horizontal kne(.*?)</dl>', p, re.DOTALL)
        x2 = re.findall('class="audio tts trackable trk-audio" data-pons-lang="(.*?)"', x[0][1])

        for l in x2:
            if config.lang_from in l:
                mp3 = 'http://sounds.pons.com/audio_tts/%s/%s' % (l, x[0][0])
                break

        os.system('(cd /tmp; wget ' + mp3 + '; mpv --load-scripts=no --loop=1 --volume=40 --force-window=no ' +
                  mp3.split('/')[-1] + '; rm ' + mp3.split('/')[-1] + ') &')
    elif type == 'gtts':
        gTTS(text=word, lang=config.lang_from, slow=False).save('/tmp/gtts_word.mp3')
        os.system(
            '(mpv --load-scripts=no --loop=1 --volume=75 --force-window=no ' + '/tmp/gtts_word.mp3' + '; rm ' + '/tmp/gtts_word.mp3' + ') &')
    elif type == 'forvo':
        url = 'https://forvo.com/word/%s/%s/' % (config.lang_from, quote(word))

        try:
            data = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'}).text

            soup = BeautifulSoup(data, "lxml")
            trs = soup.find_all('article', class_='pronunciations')[0].find_all('span', class_='play')

            mp3s = ''
            for tr in trs[:2]:
                tr = tr['onclick']
                tr = re.findall('Play\((.*?)\)', tr)[0]
                tr = tr.split(',')[4].replace("'", '')
                tr = base64.b64decode(tr)
                tr = tr.decode("utf-8")

                mp3s += 'mpv --load-scripts=no --loop=1 --volume=111 --force-window=no https://audio00.forvo.com/audios/mp3/%s ; ' % tr
            os.system('(%s) &' % mp3s)
        except:
            return


# https://github.com/Boudewijn26/gTTS-token
class Token:
    """ Token (Google Translate Token)
    Generate the current token key and allows generation of tokens (tk) with it
    Python version of `token-script.js` itself from translate.google.com
    """

    SALT_1 = "+-a^+6"
    SALT_2 = "+-3^+b+-f"

    def __init__(self):
        self.token_key = None

    def calculate_token(self, text, seed=None):
        """ Calculate the request token (`tk`) of a string
        :param text: str The text to calculate a token for
        :param seed: str The seed to use. By default this is the number of hours since epoch
        """

        if seed is None:
            seed = self._get_token_key()

        [first_seed, second_seed] = seed.split(".")

        try:
            d = bytearray(text.encode('UTF-8'))
        except UnicodeDecodeError:
            # This will probably only occur when d is actually a str containing UTF-8 chars, which means we don't need
            # to encode.
            d = bytearray(text)

        a = int(first_seed)
        for value in d:
            a += value
            a = self._work_token(a, self.SALT_1)
        a = self._work_token(a, self.SALT_2)
        a ^= int(second_seed)
        if 0 > a:
            a = (a & 2147483647) + 2147483648
        a %= 1E6
        a = int(a)
        return str(a) + "." + str(a ^ int(first_seed))

    def _get_token_key(self):
        if self.token_key is not None:
            return self.token_key

        response = requests.get("https://translate.google.com/")
        tkk_expr = re.search("(tkk:.*?),", response.text)
        if not tkk_expr:
            raise ValueError(
                "Unable to find token seed! Did https://translate.google.com change?"
            )

        tkk_expr = tkk_expr.group(1)
        try:
            # Grab the token directly if already generated by function call
            result = re.search("\d{6}\.[0-9]+", tkk_expr).group(0)
        except AttributeError:
            # Generate the token using algorithm
            timestamp = calendar.timegm(time.gmtime())
            hours = int(math.floor(timestamp / 3600))
            a = re.search("a\\\\x3d(-?\d+);", tkk_expr).group(1)
            b = re.search("b\\\\x3d(-?\d+);", tkk_expr).group(1)

            result = str(hours) + "." + str(int(a) + int(b))

        self.token_key = result
        return result

    """ Functions used by the token calculation algorithm """

    def _rshift(self, val, n):
        return val >> n if val >= 0 else (val + 0x100000000) >> n

    def _work_token(self, a, seed):
        for i in range(0, len(seed) - 2, 3):
            char = seed[i + 2]
            d = ord(char[0]) - 87 if char >= "a" else int(char)
            d = self._rshift(a, d) if seed[i + 1] == "+" else a << d
            a = a + d & 4294967295 if seed[i] == "+" else a ^ d
        return a


# https://github.com/pndurette/gTTS
class gTTS:
    """ gTTS (Google Text to Speech): an interface to Google's Text to Speech API """

    # Google TTS API supports two read speeds
    # (speed <= 0.3: slow; speed > 0.3: normal; default: 1)
    class Speed:
        SLOW = 0.3
        NORMAL = 1

    GOOGLE_TTS_URL = 'https://translate.google.com/translate_tts'
    MAX_CHARS = 100  # Max characters the Google TTS API takes at a time
    LANGUAGES = {
        'af': 'Afrikaans',
        'sq': 'Albanian',
        'ar': 'Arabic',
        'hy': 'Armenian',
        'bn': 'Bengali',
        'ca': 'Catalan',
        'zh': 'Chinese',
        'zh-cn': 'Chinese (Mandarin/China)',
        'zh-tw': 'Chinese (Mandarin/Taiwan)',
        'zh-yue': 'Chinese (Cantonese)',
        'hr': 'Croatian',
        'cs': 'Czech',
        'da': 'Danish',
        'nl': 'Dutch',
        'en': 'English',
        'en-au': 'English (Australia)',
        'en-uk': 'English (United Kingdom)',
        'en-us': 'English (United States)',
        'eo': 'Esperanto',
        'fi': 'Finnish',
        'fr': 'French',
        'de': 'German',
        'el': 'Greek',
        'hi': 'Hindi',
        'hu': 'Hungarian',
        'is': 'Icelandic',
        'id': 'Indonesian',
        'it': 'Italian',
        'iw': 'Hebrew',
        'ja': 'Japanese',
        'km': 'Khmer (Cambodian)',
        'ko': 'Korean',
        'la': 'Latin',
        'lv': 'Latvian',
        'mk': 'Macedonian',
        'no': 'Norwegian',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'ro': 'Romanian',
        'ru': 'Russian',
        'sr': 'Serbian',
        'si': 'Sinhala',
        'sk': 'Slovak',
        'es': 'Spanish',
        'es-es': 'Spanish (Spain)',
        'es-us': 'Spanish (United States)',
        'sw': 'Swahili',
        'sv': 'Swedish',
        'ta': 'Tamil',
        'th': 'Thai',
        'tr': 'Turkish',
        'uk': 'Ukrainian',
        'vi': 'Vietnamese',
        'cy': 'Welsh'
    }

    def __init__(self, text, lang='en', slow=False, debug=False):
        self.debug = debug
        if lang.lower() not in self.LANGUAGES:
            raise Exception('Language not supported: %s' % lang)
        else:
            self.lang = lang.lower()

        if not text:
            raise Exception('No text to speak')
        else:
            self.text = text

        # Read speed
        if slow:
            self.speed = self.Speed().SLOW
        else:
            self.speed = self.Speed().NORMAL

        # Split text in parts
        if self._len(text) <= self.MAX_CHARS:
            text_parts = [text]
        else:
            text_parts = self._tokenize(text, self.MAX_CHARS)

        # Clean
        def strip(x):
            return x.replace('\n', '').strip()

        text_parts = [strip(x) for x in text_parts]
        text_parts = [x for x in text_parts if len(x) > 0]
        self.text_parts = text_parts

        # Google Translate token
        self.token = Token()

    def save(self, savefile):
        """ Do the Web request and save to `savefile` """
        with open(savefile, 'wb') as f:
            self.write_to_fp(f)

    def write_to_fp(self, fp):
        """ Do the Web request and save to a file-like object """
        for idx, part in enumerate(self.text_parts):
            payload = {'ie': 'UTF-8',
                       'q': part,
                       'tl': self.lang,
                       'ttsspeed': self.speed,
                       'total': len(self.text_parts),
                       'idx': idx,
                       'client': 'tw-ob',
                       'textlen': self._len(part),
                       'tk': self.token.calculate_token(part)}
            headers = {
                "Referer": "http://translate.google.com/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"
            }
            if self.debug: print(payload)
            try:
                # Disable requests' ssl verify to accomodate certain proxies and firewalls
                # Filter out urllib3's insecure warnings. We can live without ssl verify here
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore",
                                            category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
                    r = requests.get(self.GOOGLE_TTS_URL,
                                     params=payload,
                                     headers=headers,
                                     proxies=urllib.request.getproxies(),
                                     verify=False)
                if self.debug:
                    print("Headers: {}".format(r.request.headers))
                    print("Request url: {}".format(r.request.url))
                    print("Response: {}, Redirects: {}".format(r.status_code, r.history))
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024):
                    fp.write(chunk)
            except Exception as e:
                raise

    def _len(self, text):
        """ Get char len of `text`, after decoding if Python 2 """
        try:
            # Python 2
            return len(text.decode('utf8'))
        except AttributeError:
            # Python 3
            return len(text)

    def _tokenize(self, text, max_size):
        """ Tokenizer on basic roman punctuation """

        punc = "¡!()[]¿?.,;:—«»\n"
        punc_list = [re.escape(c) for c in punc]
        pattern = '|'.join(punc_list)
        parts = re.split(pattern, text)

        min_parts = []
        for p in parts:
            min_parts += self._minimize(p, " ", max_size)
        return min_parts

    def _minimize(self, thestring, delim, max_size):
        """ Recursive function that splits `thestring` in chunks
        of maximum `max_size` chars delimited by `delim`. Returns list. """

        if self._len(thestring) > max_size:
            idx = thestring.rfind(delim, 0, max_size)
            return [thestring[:idx]] + self._minimize(thestring[idx:], delim, max_size)
        else:
            return [thestring]
