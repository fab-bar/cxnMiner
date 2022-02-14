Pattern extraction
==================

From data that has been prepared as described in :doc:`utils` patterns can be
extracted and filtered to find potential constructions.

Extract patterns
----------------

Get lists of patterns and corresponding base patterns from the corpus.

.. code-block:: bash

  cxnminer extract-patterns infile outfile_patterns outfile_base encoded_dictionary config
  cxnminer extract-patterns example_data/example_data_encoded.conllu example_data/example_data_patterns.tsv example_data/example_data_base_patterns.tsv example_data/example_data_dict_filtered_encoded.json example_data/example_config.json

Options
~~~~~~~

infile
  The name of the file that contains the encoded text in the conllu format.
  If the filename ends with ".gz" it is assumed to be a compressed file, otherwise it is assumed to be plain conllu.

outfile_patterns
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain a pair of pattern and basepattern in each line. If the filename ends with ".gz" the file will be compressed.

outfile_base
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain a pair of basepattern and the id of the sentence in which it appeared in each line. If the filename ends with ".gz" the file will be compressed.

encoded_dictionaries
  Encoded dictionaries as described in :ref:`encode-dictionary`.

config
  The configuration for construction mining as described in :doc:`settings`.

--keep_only_word
  Keep only patterns with the given word.

--keep_only_dict_words
  Removes all patterns that contain an element which is not contained in the dictionary. This does not remove patterns which contain the special element "__unknown__" which might has been introduced during the preparation of the data due to filtering the dicitionary.

--skip_unknown
  Removes all patterns that contain the element "__unknown__".


Afterwards the lists of patterns and base patterns can be converted to pattern
sets for further processing.

For this the lists needs to be sorted. This can be done, e.g., with the
following commands. `LC_ALL=c` is added in order to assure that punctation
symbols are not ignored:

.. code-block:: bash

  LC_ALL=c sort example_data/example_data_patterns.tsv > example_data/example_data_patterns_sorted.tsv
  LC_ALL=c sort example_data/example_data_base_patterns.tsv > example_data/example_data_base_patterns_sorted.tsv

The sorted lists are converted using the following command:

.. code-block:: bash

  cxnminer utils convert-pattern-list infile outfile
  cxnminer utils convert-pattern-list example_data/example_data_base_patterns_sorted.tsv example_data/example_data_base_pattern_set.jsonl
  cxnminer utils convert-pattern-list example_data/example_data_patterns_sorted.tsv example_data/example_data_pattern_set.jsonl

Options
~~~~~~~

infile
  The name of the file that contains the list of patterns or base patterns.
  If the filename ends with ".gz" it is assumed to be a compressed file, otherwise it is assumed to be plain conllu.

outfile
  The name of the file that is created by the script (if it exists, it will be overwritten).
  It will contain the a (base) pattern in each line. The patterns are represented using json (see `JSON lines <https://jsonlines.org/>`_). If the filename ends with ".gz" the file will be compressed.

--remove_hapax
  This removes patterns that only appear with one base pattern.
  Please note, that this is a different criterion than filtering using the
  frequency, since the frequency is based on sentences and not base patterns.


Get statistics about patterns
-----------------------------

For finding relevant patterns, the pattern set can be enriched with statistics
about the patterns. Applying the command `add-pattern-stats` to an encoded set
of patterns and corresponding basepatterns collects simple statistics like
frequency.

.. code-block:: bash

  cxnminer utils add-pattern-stats example_data/example_data_pattern_set.jsonl example_data/example_data_patterns_simple_stats.json --base_patterns example_data/example_data_base_pattern_set.jsonl

These statistics can then be used to filter the patterns, e.g. by removing
patterns that appear only once:

.. code-block:: bash

  cxnminer utils filter-patterns example_data/example_data_pattern_set.jsonl example_data/example_data_patterns_simple_stats.json frequency 2 example_data/example_data_pattern_set_frequent.jsonl

The relation between the given statistics and the threshold can be defined by
adding the option `--operator` which defaults to `>=`.

In order to collect statistics that need access to the individual elements of the patterns, e.g., the schematicity, the pattern set has to be decoded:

.. code-block:: bash

  cxnminer utils decode-patterns example_data/example_data_pattern_set_frequent.jsonl example_data/example_data_encoder example_data/example_data_pattern_set_frequent_decoded --processes 4

After having decoded the pattern set, further statistics can be collected:

.. code-block:: bash

  cxnminer utils get-vocabulary-probs example_data/example_data_dict.json example_data/example_data_dictionary_probs.json
  cxnminer utils get-pattern-type-freq example_data/example_data_pattern_set_frequent_decoded example_data/example_data_patterns_simple_stats.json example_data/example_data_pattern_set_frequent_type_frequencies.json
  cxnminer utils add-pattern-stats example_data/example_data_pattern_set_frequent.jsonl example_data/example_data_patterns_stats.json --decoded_patterns example_data/example_data_pattern_set_frequent_decoded --config example_data/example_config.json --vocabulary_probs example_data/example_data_dictionary_probs.json --known_stats example_data/example_data_patterns_simple_stats.json --pattern_profile_frequency example_data/example_data_pattern_set_frequent_type_frequencies.json


Get best patterns
-----------------

After having collected patterns and statistics about them, these statistics can
be used for further filtering the pattern set and extract patterns that are
likely constructions. E.g., UIF-PMI, the measure proposed by
`Forsberg et al. (2014) <https://doi.org/10.1075/cf.6.1.07for>`_,
can be used with the following command to get a decoded pattern set containing
the 2 patterns with the highest UIF-PMI value with 1 corresponding instantiation
(base pattern) that appears most frequently in the data:


.. code-block:: bash

  cxnminer utils get-top-n example_data/example_data_pattern_set_frequent.jsonl example_data/example_data_patterns_stats.json uif-pmi 2 example_data/example_data_pattern_set_top_2_uifpmi.jsonl
  cxnminer utils get-top-n-base-patterns example_data/example_data_pattern_set_top_2_uifpmi.jsonl example_data/example_data_base_pattern_set.jsonl 1 example_data/example_data_pattern_set_top_2_uifpmi_basesel_1.jsonl --example_ids example_data/example_data_pattern_set_top_2_uifpmi_basesel_1_exampleids.json
  cxnminer utils decode-pattern-collection example_data/example_data_pattern_set_top_2_uifpmi_basesel_1.jsonl example_data/example_data_encoder example_data/example_data_pattern_set_top_2_uifpmi_basesel_1_decoded.jsonl --string 
  cxnminer corpus2sentences example_data/example_data.conllu example_data/sentences --example_ids example_data/example_data_pattern_set_top_2_uifpmi_basesel_1_exampleids.json
