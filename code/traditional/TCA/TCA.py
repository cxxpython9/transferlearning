# encoding=utf-8
"""
    Created on 21:29 2018/11/12 
    @author: Jindong Wang
"""
import numpy as np
import scipy.io
import scipy.linalg
import sklearn.metrics
import sklearn.neighbors


def kernel(ker, X, X2, gamma):
    if not ker or ker == 'primal':
        return X
    elif ker == 'linear':
        if not X2:
            K = np.dot(X.T, X)
        else:
            K = np.dot(X.T, X2)
    elif ker == 'rbf':
        n1sq = np.sum(X ** 2, axis=0)
        n1 = X.shape[1]
        if not X2:
            D = (np.ones((n1, 1)) * n1sq).T + np.ones((n1, 1)) * n1sq - 2 * np.dot(X.T, X)
        else:
            n2sq = np.sum(X2 ** 2, axis=0)
            n2 = X2.shape[1]
            D = (np.ones((n2, 1)) * n1sq).T + np.ones((n1, 1)) * n2sq - 2 * np.dot(X.T, X)
        K = np.exp(-gamma * D)
    elif ker == 'sam':
        if not X2:
            D = np.dot(X.T, X)
        else:
            D = np.dot(X.T, X2)
        K = np.exp(-gamma * np.arccos(D) ** 2)
    return K


class TCA:
    def __init__(self, kernel_type='primal', dim=30, lamb=1, gamma=1):
        '''
        Init func
        :param kernel_type: kernel, values: 'primal' | 'linear' | 'rbf' | 'sam'
        :param dim: dimension after transfer
        :param lamb: lambda value in equation
        :param gamma: kernel bandwidth for rbf kernel
        '''
        self.kernel_type = kernel_type
        self.dim = dim
        self.lamb = lamb
        self.gamma = gamma

    def fit(self, Xs, Xt):
        '''
        Transform Xs and Xt
        :param Xs: ns * n_feature, source feature
        :param Xt: nt * n_feature, target feature
        :return: Xs_new and Xt_new after TCA
        '''
        X = np.hstack((Xs.T, Xt.T))
        X /= np.linalg.norm(X, axis=0)
        m, n = X.shape
        ns, nt = len(Xs), len(Xt)
        e = np.vstack((1 / ns * np.ones((ns, 1)), -1 / nt * np.ones((nt, 1))))
        M = e * e.T
        M = M / np.linalg.norm(M, 'fro')
        H = np.eye(n) - 1 / n * np.ones((n, n))
        K = kernel(self.kernel_type, X, None, gamma=self.gamma)
        n_eye = m if self.kernel_type == 'primal' else n
        a, b = np.linalg.multi_dot([K, M, K.T]) + self.lamb * np.eye(n_eye), np.linalg.multi_dot([K, H, K.T])
        w, V = scipy.linalg.eig(a, b)
        ind = np.argsort(w)
        A = V[:, ind[:self.dim]]
        Z = np.dot(A.T, K)
        Z /= np.linalg.norm(Z, axis=0)
        Xs_new, Xt_new = Z[:, :ns].T, Z[:, ns:].T
        return Xs_new, Xt_new

    def fit_predict(self, Xs, Ys, Xt, Yt):
        '''
        Transform Xs and Xt, then make predictions on target using 1NN
        :param Xs: ns * n_feature, source feature
        :param Ys: ns * 1, source label
        :param Xt: nt * n_feature, target feature
        :param Yt: nt * 1, target label
        :return: Accuracy and predicted_labels on the target domain
        '''
        Xs_new, Xt_new = self.fit(Xs, Xt)
        clf = sklearn.neighbors.KNeighborsClassifier(n_neighbors=1)
        clf.fit(Xs_new, Ys.ravel())
        y_pred = clf.predict(Xt_new)
        acc = sklearn.metrics.accuracy_score(Yt, y_pred)
        return acc, y_pred


if __name__ == '__main__':
    domains = ['caltech.mat', 'amazon.mat', 'webcam.mat', 'dslr.mat']
    for i in range(4):
        for j in range(4):
            if i != j:
                src, tar = 'data/' + domains[i], 'data/' + domains[j]
                src_domain, tar_domain = scipy.io.loadmat(src), scipy.io.loadmat(tar)
                Xs, Ys, Xt, Yt = src_domain['feas'], src_domain['label'], tar_domain['feas'], tar_domain['label']
                tca = TCA(kernel_type='primal', dim=30, lamb=1, gamma=1)
                acc, ypre = tca.fit_predict(Xs, Ys, Xt, Yt)
                print(acc)
