import gzip
import multiprocessing


class MultiprocessMap(object):

    def __init__(self, processes, chunksize=10):

        self.pool = None

        if processes > 0:
            self.pool = multiprocessing.Pool(processes)
            self.chunksize = chunksize

    def __enter__(self):

        if self.pool is not None:
            return lambda x, y: self.pool.imap(x, y, chunksize=self.chunksize)
        else:
            return lambda x,y: map(x, y)

    def __exit__(self, type, value, traceback):

        if self.pool is not None:
            self.pool.__exit__(type, value, traceback)



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
