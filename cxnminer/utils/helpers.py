import gzip
import json
import multiprocessing

from factory_manager import FactoryManager

from cxnminer.extractor import PatternExtractor


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

    def __exit__(self, exception_type, exception_value, traceback):

        if self.pool is not None:

            if exception_type is not None:
                ## let the pools __exit__ method handle exceptions
                return self.pool.__exit__(exception_type, exception_value, traceback)

            self.pool.close()
            self.pool.join()



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


def open_json_config(config):

    try:
        return json.loads(config)
    except json.JSONDecodeError:
        with open(config) as config_file:
            return json.load(config_file)


factories = FactoryManager()
factories.add_object_hierarchy("extractor", PatternExtractor)
