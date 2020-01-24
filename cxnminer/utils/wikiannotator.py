import abc
import collections

import conllu
import spacy

class Annotator(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def annotate_text(self, text, textname, sentence_filter):
        """Tokenize and annotate the text.

        Args:
            text (str): The text to be annotated.
            textname (str): The name of the text.
            sentence_filter (callable): A callable that is called for each sentence (a list of tokens).
                If it returns true, the sentence is skipped.

        Returns:
            sentences: List of annotated sentences as conllu.TokenList.
        """
        pass

    @staticmethod
    def createAnnotator(annotator_name, options):

        if annotator_name == 'spacy':
            return SpacyAnnotator(**options)
        else:
            raise ValueError(annotator_name + " is not an existing annotator.")

class SpacyAnnotator(Annotator):

    def __init__(self, model_name):

        self.annotator = spacy.load(model_name)

    def annotate_text(self, text, textname, sentence_filter):

        sentences = []
        sent_id = 1

        doc = self.annotator(text)
        for sent in doc.sents:
            if sentence_filter([token.text for token in sent]):
                continue

            sentence = []
            for tok_id, token in enumerate(sent):
                if not token.is_space:
                    sentence.append(
                        collections.OrderedDict(
                            [
                                ('id', tok_id + 1),
                                ('form', token.text),
                                ('lemma', token.lemma_),
                                ('upostag', token.pos_),
                                ('xpostag', token.tag_),
                                ('feats', '_'),
                                ('head', token.head.i - sent[0].i + 1 if token.dep_ != "ROOT" else 0),
                                ('deprel', token.dep_),
                                ('deps', '_'),
                                ('misc', '_')
                            ]
                        ))

            sentences.append(conllu.TokenList(sentence, metadata=collections.OrderedDict([('sent_id', textname + '.' + str(sent_id) )])))
            sent_id += 1

        return sentences

