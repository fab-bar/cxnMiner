Settings for the pattern extraction
===================================

The main configuration for mining constructions with cxnMiner needs to be given
either directly as `json <https://www.json.org/>`_ or as a file containing json.
The following options need to be set:

word_level
  The name of the column from the conllu data that is used for words in patterns.

levels
  Additional levels to extract for hybrid n-grams. This can be any of the following:

   form
     the plain form of the token
   lemma
     the lemma
   upos
     the universal part-of-speech tag
   xpos
     the language specific part-of-speech tag
   np_function
     the dependency relation for tokens with given `upos` tags (see `phrase_tags` below).

   Do not include the word_level in this list. It is added automatically.

phrase_tags
  Here a list of POS tags can be given. Whenever a token with one of these tags in the column `upos` is seen, the corresponding subtree is also collapsed into a single node during the pattern extraction. This allows to approximate phrases in the patterns.

unknown
  Represent unknown elements with the given string. Unknown elements appear when
  the vocabulary is extracted from a corpus that is different from the corpus
  used to extract pattern or because the items have been removed when filtering
  the vocabulary (:ref:`filter-dictionary`).

extractor
  A json object containing the settings for the extractor that is used to extract the patterns.


Pattern extractor
-----------------

A pattern extractor is used to to extract patterns from a given sentence. For
now the only available extractor is an extractor for syntactic (hybrid) n-grams.
For a description of syntactic n-grams see `Sidorov (2019)
<https://doi.org/10.1007/978-3-030-14771-6>`_.

An example json object used to represent a syntactic n-gram extractor in the
config is given below:

.. code-block:: json

  {
    "type": "sngram",
    "options": {
      "max_size": 8,
      "left_bracket": "[",
      "right_bracket": "]",
      "comma": ","
    }
  }


The extractor takes the following options:

max_size
  Upper limit for the size of the patterns.
left_bracket, right_bracket, comma
  These options allow to adapt some elements of the meta language as described by `Sidorov (2019) <https://doi.org/10.1007/978-3-030-14771-6_11>`_ for the representation of syntactic n-grams.
