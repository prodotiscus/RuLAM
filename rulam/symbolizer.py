from transliterate import translit
import re


class CannotProcessFeatureException(Exception):
    pass


class SimplestSymbolizer:
    def __init__(self, node):
        self.node = node
        self.features = None
    
    def symb(self):
        result = translit(self.node["lemma"], "ru", reversed=True)
        # TODO(sfedia): ???
        result = re.sub('[^a-z]', '', result)
        return result
    
    def symbolize_feature(self, feature_name):
        if self.features is None:
            self.features = self._process_features()

        if feature_name == "Gender":
            return self._gender_symbolize()
        
        raise CannotProcessFeatureException
    
    def _process_features(self):
        return dict(feat.split("=") for feat in self.node["feats"].split("|"))
    
    def _gender_symbolize(self):
        if self.features["Gender"] == "Masc":
            return "MALE"
        elif self.features["Gender"] == "Fem":
            return "FEMALE"
        elif self.features["Gender"] == "Neut":
            return "NEUT"
        raise ValueError
