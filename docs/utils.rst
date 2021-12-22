Data preparation
================

*cxnMiner* takes an annotated corpus in
`CoNNL-U format <https://universaldependencies.org/format.html>`_ as input.

Download and annotate Wikipedia dumps
-------------------------------------

*cxnMiner* uses an annotated corpus to automatically identify constructions.
One example for a text collection that can be used is Wikipedia.
The following commands retrieve the latest German Wikipedia dump and then extract the texts using
`segment_wiki <https://radimrehurek.com/gensim/scripts/segment_wiki.html>`_ 

.. code-block:: bash

  wget -P data/ https://dumps.wikimedia.org/dewiki/latest/dewiki-latest-pages-articles.xml.bz2
  python -m gensim.scripts.segment_wiki -f data/dewiki-latest-pages-articles.xml.bz2 -o data/dewiki-latest.json.gz

The package *cxnminer* comes with a tool to annotate the text in the format that is output by :code:`segement_wiki`.
The output of the tool is in CoNNL-U format as expected for construction mining.

Call this script using:

.. code-block:: bash

  bin/process_wiki_data infile outfile '{"annotator": "spacy", "annotator_options": {"model_name": "de_core_news_sm"}, "exclude_sections": ["Literatur", "Weblinks", "Einzelnachweise"], "max_sent_len": 70}' --logging_config='{"handlers": { "h":{ "level": "DEBUG", "class": "logging.FileHandler", "filename": "logfile.txt", "mode": "w", "formatter": "f"}}}'"

Options
~~~~~~~

infile
  The name of the file that contains the text in a json format.
  If the filename ends with ".gz" it is assumed to be a compressed file, otherwise it is assumed to be plain text json.

outfile
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain the annotated corpus in CoNNL-U format. If the filename ends with ".gz" the file will be compressed.

config
  Config expects a json-object with the following entries:

   annotator
     the name of an annotator (see below)
   annotator_options
     a json-object with options for the selected annotator
   exclude_sections
     a list with section names that should be removed (e.g. *References*)
   max_sent_len
     optional, default: 70;
     sentences longer than this are skipped

--loging_config
  Optionally the logging configuration can be set. logging_config expects a json object that represents a dict as used for `logger configuration <https://docs.python.org/3/library/logging.config.html#logging-config-dictschema>`_.

Annotators
~~~~~~~~~~

spacy
  Uses `spacy <https://spacy.io/>`_. It expects the following options:

   model_name
     the name of a model that is used. It has to be available in the
     current environment (See the `spacy documentaiton
     <https://spacy.io/usage/models>`_ for more information on installing
     models).

Encode data
-----------

For the extraction of constructions, the constructions need to be encoded efficiently
using `Huffman coding <https://en.wikipedia.org/wiki/Huffman_coding>`_.
This is done in several steps.

Extract dictionary
~~~~~~~~~~~~~~~~~~

Extract a dictionary of possible pattern elements to create an encoder.

.. code-block:: bash

  bin/extract_vocabulary infile outfile config
  bin/extract_vocabulary example_data/example_data.conllu example_data/example_data_dict.json example_data/example_config.json

Options
+++++++

infile
  The name of the file that contains the annotated corpus in CoNLL-U format.
  If the filename ends with ".gz" it is assumed to be a compressed file.

outfile
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain the vocabulary for the given levels in json format.
  If the filename ends with ".gz" the file will be compressed.

config
  The configuration for construction mining as described in :doc:`settings`.

--drop_frequencies
  The list can contain the frequencies (needed to create a `Huffman encoder`) or they can optionally be dropped.

.. _filter-dictionary:

Filter dictionary
~~~~~~~~~~~~~~~~~

Remove items with a frequency below a given threshold from an extracted dictionary.

.. code-block:: bash

  bin/filter_vocabulary dictionaries outfile min_frequency
  bin/filter_vocabulary example_data/example_data_dict.json example_data/example_data_dict_filtered.json 2

Options
+++++++

dictionaries
  The name of the file that contains the dictionary (including frequencies) extracted from the corpus.
  If the filename ends with ".gz" it is assumed to be a compressed file.

outfile
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain the filtered vocabulary json format.
  If the filename ends with ".gz" the file will be compressed.

min_frequency
  Items with a lower frequency will be dropped from the dictionary.

Prepare encoder
~~~~~~~~~~~~~~~

Create and pickle an encoder based on an extracted dictionary.

.. code-block:: bash

  bin/create_encoder dictionaries outfile config
  bin/create_encoder example_data/example_data_dict_filtered.json example_data/example_data_encoder example_data/example_config.json

Options
+++++++

dictionaries
  The name of the file that contains the dictionary extracted from the corpus.
  If the filename ends with ".gz" it is assumed to be a compressed file.

outfile
  The pickled encoder.
  If the filename ends with ".gz" the file will be compressed.

config
  The configuration for construction mining as described in :doc:`settings`.

.. _encode-dictionary:

Encode dictionary
~~~~~~~~~~~~~~~~~

Encodes the complete dictionary - creating a dictionary that can be used
to encode the corpus using lookup.

.. code-block:: bash

  bin/encode_vocabulary vocabulary outfile encoder config
  bin/encode_vocabulary example_data/example_data_dict_filtered.json example_data/example_data_dict_filtered_encoded.json example_data/example_data_encoder example_data/example_config.json

Options
+++++++

vocabulary
  Either the name of the file that contains the dictionary extracted from the corpus.
  If the filename ends with ".gz" it is assumed to be a compressed file.
  Or a json-String containing the vocabulary directly.

outfile
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain a lookup table for the vocabulary and the encoded versions in json format.
  If the filename ends with ".gz" the file will be compressed.

encoder
  The pickled encoder.

config
  The configuration for construction mining as described in :doc:`settings`.

--no_frequencies
  Add this flag if the dictionary does not contain frequencies.

--loging_config
  See above.

.. _encode-corpus:

Encode corpus
~~~~~~~~~~~~~

To make the pattern extraction more efficient, the corpus can be pre-encoded.
Uses an encoded dicitionary to efficiently encode the corpus.

.. code-block:: bash

  bin/encode_corpus infile outfile dictionary config
  bin/encode_corpus example_data/example_data.conllu example_data/example_data_encoded.conllu example_data/example_data_dict_filtered_encoded.json example_data/example_config.json

Options
+++++++

infile
  The name of the file that contains the annotated corpus in CoNLL-U format.
  If the filename ends with ".gz" it is assumed to be a compressed file.

outfile
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain the annotated corpus in CoNNL-U format with encoded levels.
  If the filename ends with ".gz" the file will be compressed.

dictionary
  The encoded dictionary.

config
  The configuration for construction mining as described in :doc:`settings`.

--processes
  Controls the number of processes to be used.

--loging_config
  See above.
