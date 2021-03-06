# -*- coding: utf-8 -*-
"""
@author: Vladya
"""

import urllib
from os import path
from .. import (
    translator_abstract,
    current_session
)
from . import (
    utils,
    consts,
    _paths,
    LOGGER
)


try:
    import urllib3
except ImportError:
    from requests.packages import urllib3


class Translator(translator_abstract.TranslatorAbstract):

    __version__ = "1.1.0"

    LOGGER = LOGGER.getChild("Translator")
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u"translations.json")
    LOCAL_DATABASE_FN = path.join(
        _paths.LOCAL_DATABASE_FOLDER,
        u"translations.json"
    )

    HOSTNAME = "clients5.google.com"

    SYMB_LIMIT = 5000

    def __init__(self):
        super(Translator, self).__init__()

    def get_base_url(self):
        return urllib3.util.Url(
            scheme='https',
            auth=None,
            host=self.HOSTNAME,
            port=None,
            path="/translate_a/t",
            query=None,
            fragment=None
        )

    def get_lang_code(self, data):
        return utils._get_lang_code(data)

    def get_lang_name(self, data):
        return utils._get_lang_name(data)

    def get_all_lang_codes(self):
        for code in consts.LANG_CODES.iterkeys():
            yield code

    def translate(self, text, dest, src, _update_on_hdd=True):

        dest, src = map(self.get_lang_code, (dest, src))
        text = text.strip()

        if not text:
            return u""

        if not isinstance(text, unicode):
            text = text.decode("utf_8", "ignore")

        parts = tuple(self.get_parts_from_text(text))
        if len(parts) > 1:

            def _translate_child(txt):
                return self.translate(txt, dest, src, _update_on_hdd)

            return self.join_parts_to_text(map(_translate_child, parts))

        elif not parts:
            return u""

        text = parts[0]
        if len(text) >= self.SYMB_LIMIT:
            text = u"{0}...".format(text[:(self.SYMB_LIMIT - 4)].strip())

        _text_for_log = text
        if len(_text_for_log) >= 100:
            _text_for_log = u"{0}...".format(_text_for_log[:96].strip())

        with self._database_lock:

            self.LOGGER.debug(
                "Start translating \"%s\" from %s to %s.",
                _text_for_log.encode("utf_8", "ignore"),
                self.get_lang_name(src).lower(),
                self.get_lang_name(dest).lower()
            )

            _lang_db = self._database.setdefault(src, {})
            _text_db = _lang_db.setdefault(text, {})

            if dest in _text_db:
                result = _text_db[dest]
                self.add_translate_to_local_database(
                    text,
                    dest,
                    src,
                    result,
                    _update_on_hdd
                )
                self.LOGGER.debug("Translation is available in database.")
                return result

            self.LOGGER.debug("Translation is not available in database.")

            result = self._web_translate(text, dest, src)
            self.LOGGER.debug("Successfully translated.")

            _text_db[dest] = result
            self.add_translate_to_local_database(
                text,
                dest,
                src,
                result,
                False
            )

            if _update_on_hdd:
                self.backup_database()

            return result

    def _web_translate(self, text, dest, src):

        dest, src = map(self.get_lang_code, (dest, src))
        params = {
            "client": "dict-chrome-ex",
            "sl": src,
            "tl": dest,
            "q": text.encode("utf_8", "ignore")
        }

        base_url = self.get_base_url()
        url = urllib3.util.Url(
            scheme=base_url.scheme,
            auth=base_url.auth,
            host=base_url.host,
            port=base_url.port,
            path=base_url.path,
            query=urllib.urlencode(params),
            fragment=base_url.fragment
        ).url

        request = current_session.get(url)
        _json = request.json()
        result = ""
        for answer in _json["sentences"]:
            if "trans" in answer:
                result += answer["trans"]
        return result
