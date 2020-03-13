import gzip

def open_file(filename, mode='r', encoding='utf-8'):

    if filename.endswith(".gz"):

        ## gzip opens in binary mode by default
        ## assure text mode if binary mode is not explicitely requested
        if 'b' not in mode and 't' not in mode:
            return gzip.open(filename, mode + 't', encoding=encoding)
        else:
            return gzip.open(filename, mode)

    else:

        if 'b' not in mode:
            return open(filename, mode, encoding=encoding)
        else:
            return open(filename, mode)
