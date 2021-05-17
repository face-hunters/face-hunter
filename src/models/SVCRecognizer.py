import pickle
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder


class SVCRecognizer():
    def __init__(self):
        self.estimator = None
        self.le = None

    def tune_hyperparameters(self):
        # tooooooo tired.....gonna to later
        pass

    def fit(self, embeddings, labels, model_path='data/embeddings/svm.pickle', le_path='data/embeddings/le.pickle'):
        # load from local
        if os.path.exists(model_path) and os.path.exists(le_path):
            self.estimator = pickle.loads(open(model_path, "rb").read())
            self.le = pickle.loads(open(le_path, "rb").read())
        else:
            # create
            self.estimator = SVC(C=1.0, kernel="linear", probability=True)
            self.le = LabelEncoder()
            self.estimator.fit(embeddings, self.le.fit_transform(labels))

            # save to local
            with open(model_path, 'wb') as f:
                f.write(pickle.dumps(self.estimator))
            with open(le_path, 'wb') as f:
                f.write(pickle.dumps(self.le))

    def predict(self, embedding, threshold=0.01):
        T = 1 - threshold

        predictions = self.estimator.predict_proba(embedding)[0]
        max_proba_index = np.argmax(predictions)
        proba = predictions[max_proba_index]
        y = self.le.classes_[max_proba_index]

        # if proba < T:  # filter false positive recognition
        # y = None

        return y