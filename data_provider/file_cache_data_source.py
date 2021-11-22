from typing import List

CACHE_DIR_PATH = "urls/"


def store_in_local(file_path: str, pairs_list: List[List[str]]) -> None:
    print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs_list), file=open(file_path, 'a'))
    print('\n' + '=====/////-----' + '\n', file=open(file_path, 'a'))


def get_from_local(file_path: str) -> List[List[str]]:
    pairs_list = []
    lines = open(file_path).read().split('=====/////-----')
    if len(lines[0].strip()):
        for pair in lines[0].strip().split('\n\n'):
            pair = pair.split('\n')
            pairs_list.append([pair[0], pair[1]])

    return pairs_list
