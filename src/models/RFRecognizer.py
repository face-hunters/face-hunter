from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
import pickle


class RFRecognizer():
    def __init__(self):
        self.estimator = None
        self.le = None

    # def tune_hyperparameters(self, embeddings, labels):
    #   n_estimators = range(200)
    #   criterion = ["gini", "entropy"]
    #   parameter_space = {
    #       "criterion": criterion,
    #       "min_samples_leaf": [2, 4, 6],
    #       "n_estimators": n_estimators
    #   }
    #   clf = GridSearchCV(RandomForestClassifier(), parameter_space, cv=5)
    #   clf.fit(embeddings,self.le.fit_transform(labels))
    #   self.estimator = clf.best_estimator_
    def fit(self, embeddings, labels, model_path='data/embeddings/rf.pickle', le_path='data/embeddings/le.pickle'):
        # load from local
        if os.path.exists(model_path) and os.path.exists(le_path):
            self.estimator = pickle.loads(open(model_path, "rb").read())
            self.le = pickle.loads(open(le_path, "rb").read())
        else:
            # create
            self.le = LabelEncoder()
            n_estimators = [5, 20, 50, 100]
            criterion = ["gini", "entropy"]
            parameter_space = {
                "criterion": criterion,
                "min_samples_leaf": [2, 4, 6],
                "n_estimators": n_estimators
            }
            clf = GridSearchCV(RandomForestClassifier(), parameter_space, cv=2)
            clf.fit(embeddings, self.le.fit_transform(labels))
            self.estimator = clf.best_estimator_
            # save to local
            with open(model_path, 'wb') as f:
                f.write(pickle.dumps(self.estimator))
            with open(le_path, 'wb') as f:
                f.write(pickle.dumps(self.le))

    def predict(self, embedding, probe_threshold=0.1):
        probability = self.estimator.predict_proba(embedding)[0]
        if max(probability) >= probe_threshold:
            return self.le.classes_[self.estimator.predict(embedding)[0]]
        else:
            LOGGER.info('face detected but no match in Random Forest')
            return None
