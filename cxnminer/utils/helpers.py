import gzip

def open_file(filename, mode='r', encoding='utf-8'):

    if filename.endswith(".gz"):
        return gzip.open(filename, mode + 't', encoding=encoding)
    else:
        return open(filename, mode, encoding=encoding)
