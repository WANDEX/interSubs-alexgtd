import ast
import math
import os
import re
import time
from json import loads
from urllib.parse import quote

import requests

import config


# https://github.com/ssut/py-googletrans
class TokenAcquirer_DISABLED:
    """Google Translate API token generator

    translate.google.com uses a token to authorize the requests. If you are
    not Google, you do have this token and will have to pay for use.
    This class is the result of reverse engineering on the obfuscated and
    minified code used by Google to generate such token.

    The token is based on a seed which is updated once per hour and on the
    text that will be translated.
    Both are combined - by some strange math - in order to generate a final
    token (e.g. 744915.856682) which is used by the API to validate the
    request.

    This operation will cause an additional request to get an initial
    token from translate.google.com.

    Example usage:
        >>> from googletrans.gtoken import TokenAcquirer
        >>> acquirer = TokenAcquirer()
        >>> text = 'test'
        >>> tk = acquirer.do(text)
        >>> tk
        950629.577246
    """
    import httpx
    def rshift(self, val, n):
        """python port for '>>>'(right shift with padding)
        """
        return (val % 0x100000000) >> n

    RE_TKK = re.compile(r'tkk:\'(.+?)\'', re.DOTALL)
    RE_RAWTKK = re.compile(r'tkk:\'(.+?)\'', re.DOTALL)

    def __init__(self, client=httpx, tkk='0', host='translate.googleapis.com'):
        self.client = client
        self.tkk = tkk
        self.host = host if 'http' in host else 'http://' + host

    def _update(self):
        """update tkk
        """
        # we don't need to update the base TKK value when it is still valid
        now = math.floor(int(time.time() * 1000) / 3600000.0)
        if self.tkk and int(self.tkk.split('.')[0]) == now:
            return

        r = self.client.get(self.host)

        raw_tkk = self.RE_TKK.search(r.text)
        if raw_tkk:
            self.tkk = raw_tkk.group(1)
            return

        try:
            # this will be the same as python code after stripping out a reserved word 'var'
            code = self.RE_TKK.search(r.text).group(1).replace('var ', '')
            # unescape special ascii characters such like a \x3d(=)
            code = code.encode().decode('unicode-escape')
        except AttributeError:
            raise Exception(
                'Could not find TKK token for this request.\nSee https://github.com/ssut/py-googletrans/issues/234 for more details.')
        except:
            raise

        if code:
            tree = ast.parse(code)
            visit_return = False
            operator = '+'
            n, keys = 0, dict(a=0, b=0)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    name = node.targets[0].id
                    if name in keys:
                        if isinstance(node.value, ast.Num):
                            keys[name] = node.value.n
                        # the value can sometimes be negative
                        elif isinstance(node.value, ast.UnaryOp) and \
                                isinstance(node.value.op, ast.USub):  # pragma: nocover
                            keys[name] = -node.value.operand.n
                elif isinstance(node, ast.Return):
                    # parameters should be set after this point
                    visit_return = True
                elif visit_return and isinstance(node, ast.Num):
                    n = node.n
                elif visit_return and n > 0:
                    # the default operator is '+' but implement some more for
                    # all possible scenarios
                    if isinstance(node, ast.Add):  # pragma: nocover
                        pass
                    elif isinstance(node, ast.Sub):  # pragma: nocover
                        operator = '-'
                    elif isinstance(node, ast.Mult):  # pragma: nocover
                        operator = '*'
                    elif isinstance(node, ast.Pow):  # pragma: nocover
                        operator = '**'
                    elif isinstance(node, ast.BitXor):  # pragma: nocover
                        operator = '^'
            # a safety way to avoid Exceptions
            clause = compile('{1}{0}{2}'.format(
                operator, keys['a'], keys['b']), '', 'eval')
            value = eval(clause, dict(__builtin__={}))
            result = '{}.{}'.format(n, value)

            self.tkk = result

    def _lazy(self, value):
        """like lazy evaluation, this method returns a lambda function that
        returns value given.
        We won't be needing this because this seems to have been built for
        code obfuscation.

        the original code of this method is as follows:

           ... code-block: javascript

               var ek = function(a) {
                return function() {
                    return a;
                };
               }
        """
        return lambda: value

    def _xr(self, a, b):
        size_b = len(b)
        c = 0
        while c < size_b - 2:
            d = b[c + 2]
            d = ord(d[0]) - 87 if 'a' <= d else int(d)
            d = rshift(a, d) if '+' == b[c + 1] else a << d
            a = a + d & 4294967295 if '+' == b[c] else a ^ d

            c += 3
        return a

    def acquire(self, text):
        a = []
        # Convert text to ints
        for i in text:
            val = ord(i)
            if val < 0x10000:
                a += [val]
            else:
                # Python doesn't natively use Unicode surrogates, so account for those
                a += [
                    math.floor((val - 0x10000) / 0x400 + 0xD800),
                    math.floor((val - 0x10000) % 0x400 + 0xDC00)
                ]

        b = self.tkk if self.tkk != '0' else ''
        d = b.split('.')
        b = int(d[0]) if len(d) > 1 else 0

        # assume e means char code array
        e = []
        g = 0
        size = len(a)
        while g < size:
            l = a[g]
            # just append if l is less than 128(ascii: DEL)
            if l < 128:
                e.append(l)
            # append calculated value if l is less than 2048
            else:
                if l < 2048:
                    e.append(l >> 6 | 192)
                else:
                    # append calculated value if l matches special condition
                    if (l & 64512) == 55296 and g + 1 < size and \
                            a[g + 1] & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + (a[g] & 1023)  # This bracket is important
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128)
                e.append(l & 63 | 128)
            g += 1
        a = b
        for i, value in enumerate(e):
            a += value
            a = self._xr(a, '+-a^+6')
        a = self._xr(a, '+-3^+b+-f')
        a ^= int(d[1]) if len(d) > 1 else 0
        if a < 0:  # pragma: nocover
            a = (a & 2147483647) + 2147483648
        a %= 1000000  # int(1E6)

        return '{}.{}'.format(a, a ^ b)

    def do(self, text):
        self._update()
        tk = self.acquire(text)
        return tk


# https://github.com/Saravananslb/py-googletranslation
class TokenAcquirer:
    """Google Translate API token generator

    translate.google.com uses a token to authorize the requests. If you are
    not Google, you do have this token and will have to pay for use.
    This class is the result of reverse engineering on the obfuscated and
    minified code used by Google to generate such token.

    The token is based on a seed which is updated once per hour and on the
    text that will be translated.
    Both are combined - by some strange math - in order to generate a final
    token (e.g. 464393.115905) which is used by the API to validate the
    request.

    This operation will cause an additional request to get an initial
    token from translate.google.com.

    Example usage:
        >>> from pygoogletranslation.gauthtoken import TokenAcquirer
        >>> acquirer = TokenAcquirer()
        >>> text = 'test'
        >>> tk = acquirer.do(text)
        >>> tk
        464393.115905
    """

    def __init__(self, tkk='0', tkk_url='https://translate.google.com/translate_a/element.js', proxies=None):

        if proxies is not None:
            self.proxies = proxies
        else:
            self.proxies = None

        r = requests.get(tkk_url, proxies=self.proxies)

        if r.status_code == 200:
            re_tkk = re.search("(?<=tkk=\\')[0-9.]{0,}", str(r.content.decode("utf-8")))
            if re_tkk:
                self.tkk = re_tkk.group(0)
            else:
                self.tkk = '0'
        else:
            self.tkk = '0'

    def _xr(self, a, b):
        size_b = len(b)
        c = 0
        while c < size_b - 2:
            d = b[c + 2]
            d = ord(d[0]) - 87 if 'a' <= d else int(d)
            d = self.rshift(a, d) if '+' == b[c + 1] else a << d
            a = a + d & 4294967295 if '+' == b[c] else a ^ d

            c += 3
        return a

    def acquire(self, text):
        a = []
        # Convert text to ints
        for i in text:
            val = ord(i)
            if val < 0x10000:
                a += [val]
            else:
                # Python doesn't natively use Unicode surrogates, so account for those
                a += [
                    math.floor((val - 0x10000) / 0x400 + 0xD800),
                    math.floor((val - 0x10000) % 0x400 + 0xDC00)
                ]

        b = self.tkk
        d = b.split('.')
        b = int(d[0]) if len(d) > 1 else 0

        # assume e means char code array
        e = []
        g = 0
        size = len(a)
        while g < size:
            l = a[g]
            # just append if l is less than 128(ascii: DEL)
            if l < 128:
                e.append(l)
            # append calculated value if l is less than 2048
            else:
                if l < 2048:
                    e.append(l >> 6 | 192)
                else:
                    # append calculated value if l matches special condition
                    if (l & 64512) == 55296 and g + 1 < size and \
                            a[g + 1] & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + (a[g] & 1023)  # This bracket is important
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128)
                e.append(l & 63 | 128)
            g += 1
        a = b
        for i, value in enumerate(e):
            a += value
            a = self._xr(a, '+-a^+6')
        a = self._xr(a, '+-3^+b+-f')
        a ^= int(d[1]) if len(d) > 1 else 0
        if a < 0:  # pragma: nocover
            a = (a & 2147483647) + 2147483648
        a %= 1000000  # int(1E6)
        return '{}.{}'.format(a, a ^ b)

    def do(self, text):
        tk = self.acquire(text)
        return tk

    def rshift(self, val, n):
        """python port for '>>>'(right shift with padding)
        """
        return (val % 0x100000000) >> n


def google(word):
    word = word.replace('\n', ' ').strip()
    url = 'https://translate.google.com/translate_a/single?client=t&sl={lang_from}&tl={lang_to}&hl={lang_to}&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&otf=1&pc=1&ssel=3&tsel=3&kc=2&q={word}'.format(
        lang_from=config.lang_from, lang_to=config.lang_to, word=quote(word))

    pairs = []
    fname = 'urls/' + url.replace('/', "-")
    try:
        if ' ' in word:
            raise Exception('skip saving')

        p = open(fname).read().split('=====/////-----')
        try:
            word_descr = p[1].strip()
        except:
            word_descr = ''

        for pi in p[0].strip().split('\n\n'):
            pi = pi.split('\n')
            pairs.append([pi[0], pi[1]])
    except:
        acquirer = TokenAcquirer()
        tk = acquirer.do(word)

        url = '{url}&tk={tk}'.format(url=url, tk=tk)
        p = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'}).text
        p = loads(p)

        try:
            pairs.append([p[0][0][0], p[0][0][1]])
        except:
            pass

        if p[1] != None:
            for translations in p[1]:
                for translation in translations[2]:
                    try:
                        t1 = translation[5] + ' ' + translation[0]
                    except:
                        t1 = translation[0]

                    t2 = ', '.join(translation[1])

                    if not len(t1):
                        t1 = '-'
                    if not len(t2):
                        t2 = '-'

                    pairs.append([t1, t2])

        word_descr = ''
        # extra check against double-writing from rouge threads
        if ' ' not in word and not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    return pairs, ['', '']
