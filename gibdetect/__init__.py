"""

SPECIAL THANKS TO rrenaud FOR WRITING THE ORIGINAL GIBBERISH DETECTION SCRIPT
https://github.com/rrenaud/Gibberish-Detector/blob/master/gib_detect.py

This script is adapted from the original script designed for python 2

His licence can be found this files root directory under "Original GibberishDetection LICENCE"

"""

import math
import pickle

class gibdetect(object):
    accepted_chars = 'abcdefghijklmnopqrstuvwxyz '

    pos = dict([(char, idx) for idx, char in enumerate(accepted_chars)])
    def __init__(self,filelocation):
        self.install = filelocation
        try:
            with open(f'{self.install}/gibdetect/gib_model.pki', 'r'):
                pass
        except:
            print("Gibberish detection dataset does not exist, will now train a new dataset, this may take a while")
            self.train()
            print("Dataset trained")
        finally:
            self.model_data = pickle.load(open(f'{self.install}/gibdetect/gib_model.pki', 'rb'))

    def train(self):
        """ Write a simple model as a pickle file """
        k = len(self.accepted_chars)
        counts = [[10 for i in range(0, k)] for i in range(0, k)]
        for line in open(f'{self.install}/gibdetect/big.txt'):
            for a, b in self.ngram(2, line):
                counts[self.pos[a]][self.pos[b]] += 1
        for i, row in enumerate(counts):
            s = float(sum(row))
            for j in range(0, len(row)):
                row[j] = math.log(row[j] / s)
        good_probs = [self.avg_transition_prob(l, counts) for l in open(f'{self.install}/gibdetect/good.txt')]
        bad_probs = [self.avg_transition_prob(l, counts) for l in open(f'{self.install}/gibdetect/bad.txt')]
        assert min(good_probs) > max(bad_probs)
        thresh = (min(good_probs) + max(bad_probs)) / 2
        pickle.dump({'mat': counts, 'thresh': thresh}, open(f'{self.install}/gibdetect/gib_model.pki', 'wb'))

    def normalize(self, line):
        return [c.lower() for c in line if c.lower() in self.accepted_chars]

    def ngram(self, n, l):
        """ Return all n grams from l after normalizing """
        filtered = self.normalize(l)
        for start in range(0, len(filtered) - n + 1):
            yield ''.join(filtered[start:start + n])

    def avg_transition_prob(self, l, log_prob_mat):
        """ Return the average transition prob from l through log_prob_mat. """
        log_prob = 0.0
        transition_ct = 0
        for a, b in self.ngram(2, l):
            log_prob += log_prob_mat[self.pos[a]][self.pos[b]]
            transition_ct += 1
        return math.exp(log_prob / (transition_ct or 1))

    def scan(self, detection):
        model_mat = self.model_data['mat']
        threshold = self.model_data['thresh']
        return self.avg_transition_prob(detection, model_mat) > threshold