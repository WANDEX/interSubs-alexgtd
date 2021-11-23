import requests

import config


# https://github.com/EmilioK97/pydeepl
def deepl(text):
    l1 = config.lang_from.upper()
    l2 = config.lang_to.upper()

    if len(text) > 5000:
        return 'Text too long (limited to 5000 characters).'

    parameters = {
        'jsonrpc': '2.0',
        'method': 'LMT_handle_jobs',
        'params': {
            'jobs': [
                {
                    'kind': 'default',
                    'raw_en_sentence': text
                }
            ],
            'lang': {

                'source_lang_user_selected': l1,
                'target_lang': l2
            }
        }
    }

    response = requests.post('https://www2.deepl.com/jsonrpc', json=parameters).json()
    if 'result' not in response:
        return 'DeepL call resulted in a unknown result.'

    translations = response['result']['translations']

    if len(translations) == 0 \
            or translations[0]['beams'] is None \
            or translations[0]['beams'][0]['postprocessed_sentence'] is None:
        return 'No translations found.'

    return translations[0]['beams'][0]['postprocessed_sentence']
