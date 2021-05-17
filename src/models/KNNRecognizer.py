import pickle
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from sklearn import neighbors


class KNNRecognizer():
    def __init__(self):
        self.estimator = None
        self.le = None

    def fit(self, embeddings, labels, model_path='data/embeddings/knn.pickle', le_path='data/embeddings/le.pickle'):
        # load from local
        if os.path.exists(model_path) and os.path.exists(le_path):
            self.estimator = pickle.loads(open(model_path, "rb").read())
            self.le = pickle.loads(open(le_path, "rb").read())
        else:
            # create
            self.estimator = KNeighborsClassifier()
            self.le = LabelEncoder()
            para = range(1, 10)
            param_dict = {"n_neighbors": para}
            grid_cv = GridSearchCV(self.estimator, param_grid=param_dict, cv=2)
            grid_cv.fit(embeddings, self.le.fit_transform(labels))
            self.estimator = grid_cv.best_estimator_

            # save to local
            with open(model_path, 'wb') as f:
                f.write(pickle.dumps(self.estimator))
            with open(le_path, 'wb') as f:
                f.write(pickle.dumps(self.le))

    def predict(self, embedding, threshold=0.6):
        distance, indices = self.estimator.kneighbors(embedding, n_neighbors=1)
        if distance[0][0] <= threshold:
            return self.le.classes_[self.estimator.predict(embedding)[0]]
        else:
            LOGGER.info('face detected but no match in knn')
            return None
