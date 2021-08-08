import os
import re

import interSubs_config as config


# offline dictionary with word \t translation
def tab_divided_dict(word):
    if word in offdict:
        tr = re.sub('<.*?>', '', offdict[word]) if config.tab_divided_dict_remove_tags_B else offdict[word]
        tr = tr.replace('\\n', '\n').replace('\\~', '~')
        return [[tr, '-']], ['', '']
    else:
        return [], ['', '']


if 'tab_divided_dict' in config.translation_function_names:
    offdict = {x.split('\t')[0].strip().lower(): x.split('\t')[1].strip() for x in
               open(os.path.expanduser(config.tab_divided_dict_fname)).readlines() if '\t' in x}
