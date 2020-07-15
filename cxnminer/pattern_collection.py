import collections
import json
import os.path

from cxnminer.utils.helpers import open_file

class PatternCollection:

    def __init__(self, patterns_filename):

        self.patterns_file = patterns_filename
        self.additional_content = collections.defaultdict(dict)


    def pattern_generator(self, include_id=False):

        pattern_id = 0

        with open_file(self.patterns_file) as infile:

            for line in infile:

                pattern_id += 1

                pattern, content = json.loads(line)
                content = {**content, **self.additional_content[pattern_id]}
                if include_id:
                    yield pattern_id, pattern, content
                else:
                    yield pattern, content

    def save(self):


        ## iterate over patterns and write to temp file (additional_content is included!)
        import tempfile, shutil
        with tempfile.NamedTemporaryFile(mode='w+t', delete=False) as tmpfile:
            for pattern, content in self.pattern_generator():
                json.dump((pattern, content), tmpfile)
                tmpfile.write("\n")

            tmppath = tmpfile.name

        ## move temp file to original file
        shutil.copy(tmppath, self.patterns_file)
        os.remove(tmppath)

        if hasattr(self, 'equivalence_classes'):
            json.dump({
                str(key): list(values) for key, values in
                    self.equivalence_classes.items()
            },
            open_file(self.patterns_file + '_schematization.json', 'w'))


    def loadSchematisationRelation(self):

        if hasattr(self, 'equivalence_classes'):
            ## already loaded, do nothing
            pass
        else:
            if os.path.isfile(self.patterns_file + '_schematization.json'):
                print("Load from file!")
                self.equivalence_classes = {
                    int(key): set(values) for key, values in
                    json.load(open_file(self.patterns_file + '_schematization.json')).items()
                }
            else:
                basepatterns_to_class_id = dict()
                self.equivalence_classes = collections.defaultdict(set)

                for pattern_id, pattern, content in self.pattern_generator(include_id=True):

                    basepatterns = tuple([bp[0] for bp in content['base_patterns']])
                    if basepatterns in basepatterns_to_class_id:
                        class_id = basepatterns_to_class_id[basepatterns]
                    else:
                        class_id = pattern_id
                        basepatterns_to_class_id[basepatterns] = class_id

                    self.additional_content[pattern_id]['schematization_class'] = class_id
                    self.equivalence_classes[class_id].add(pattern_id)



    ## instantions/schematisation relation
    def getSchematisationRelation(self):

        self.loadSchematizationRelation()
        return self.equivalence_classes

