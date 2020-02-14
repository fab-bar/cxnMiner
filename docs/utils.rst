Corpus preparation
==================

*cxnMiner* takes an annotated corpus in
`CoNNL-U format <https://universaldependencies.org/format.html>`_ as input.

Annotate Wikipedia dumps
------------------------

The package comes with a tool to annotate text that comes in a json format as
the script `segment_wiki
<https://radimrehurek.com/gensim/scripts/segment_wiki.html>`_ creates from a
wikipedia dump. The output of the tool is in CoNNL-U format as expected for
construction induction.

Call this script using:

.. code-block:: bash

  bin/process_wiki_data input_file output_file '{"annotator": "spacy", "annotator_options": {"model_name": "de_core_news_sm"}, "exclude_sections": ["Literatur", "Weblinks", "Einzelnachweise"], "max_sent_len": 70}' --logging_config='{"handlers": { "h":{ "level": "DEBUG", "class": "logging.FileHandler", "filename": "data/logs/dewiki-20191001-annotation.txt", "mode": "w", "formatter": "f"}}}'"

Options
~~~~~~~

input_data
  The name of the file that contains the text in a json format.
  If the filename ends with ".gz" it is assumed to be a compressed file, otherwise it is assumed to be plain text json.

output_file
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
