import sys

sys.path.append('../..')
import numpy as np
import tensorflow as tf
from random import shuffle
import json
import pickle
import definitions
from data_manager import *
from seq2seqModel.hyper_params import *


# sents_path = None
EMBED_DIM = 100
LR = 0.1
ITERNUM = 10

# def create_dict_from_path(sents_path):
#     words_list = []
#     with open(sents_path) as sents:
#         for sent in sents:
#             words = sent.rstrip().split()
#             for word in words:
#                 if word in words_list:
#                     pass
#                 else:
#                     words_list.append(word)
#     return words_list

def create_dict(sents):
    words_list = []
    for sent in sents:
        words = sent.rstrip().split()
        for word in words:
            if word in words_list:
                pass
            else:
                words_list.append(word)
    print("Longueur du vocabulaire: ")
    print(len(words_list))
    return words_list

def index_to_one_hot(index, words_list):
    size = (len(words_list))
    vec = np.zeros((size,))
    vec[index] = 1.
    return vec

# def convert_words_to_indices_from_path(sents_path):
#     newsents = []
#     with open(sents_path) as sents:
#         for sent in sents:
#             newsent = []
#             for word in sent.rstrip().split():
#                 newsent.append(words_list.index(word))
#             newsents.append(newsent)
#     return newsents

def convert_words_to_indices(sents, words_list):
    newsents = []
    for sent in sents:
        newsent = []
        for word in sent.rstrip().split():
            newsent.append(int(words_list.index(word)))
        newsents.append(newsent)
    return newsents


def get_env(k, sent):
    if k == 0:
        env = [sent[1], sent[2]]
    elif k == 1:
        env = [sent[0], sent[2], sent[3]]
    elif k == len(sent) - 1:
        env = [sent[k - 2], sent[k - 1]]
    elif k == len(sent) - 2:
        env = [sent[k - 2], sent[k - 1], sent[k + 1]]
    else:
        env = [sent[k - 2], sent[k - 1], sent[k + 1], sent[k + 2]]
    return env

def word2vec(sents, savepath, embed_dim = EMBED_DIM, iternum = ITERNUM, lr = LR):
    # takes a **list of sentences** and hyper-parameters
    # returns a dictionary of words and their embeddings
    # and saving that dictionary to a pickle file "word_embeddings"
    # params:
    #   sents - the sentences list
    #   savepath - a path to save the pickle file
    #   embed_dim - dimension of the embeddings. default: 8
    #   iternum - number of iterations over the training set. default: 3
    #   lr - learning rate of the SGD. default: 0.1

    words_list = create_dict(sents)

    onehots = tf.placeholder(tf.float32, [None, len(words_list)])
    Win = tf.get_variable("Win", shape=[len(words_list), embed_dim], initializer=tf.random_uniform_initializer(0, 1))
    h = tf.nn.tanh(tf.matmul(onehots, Win))
    Wout = tf.get_variable("Wout", shape=[embed_dim, len(words_list)], initializer=tf.random_uniform_initializer(0, 1))
    z = tf.matmul(h, Wout)
    # yt = tf.placeholder(tf.float32, [None, len(words_list)])
    yt = tf.placeholder(tf.int32, [1,])

    # yaxol lihiyot shehu mecape levector im indexim velo le-one-hot-im
    loss = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=yt, logits=z)

    opt = tf.train.GradientDescentOptimizer(lr).minimize(loss)

    newsents = convert_words_to_indices(sents, words_list)

    indices = list(range(len(newsents)))
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for i in range(iternum):
            shuffle(indices)
            for j in range(len(newsents)):
                if j % 500 == 0:
                    print('iteration number:{0}, {1} sents done'.format(i+1,j))
                currsent = newsents[indices[j]]
                for k, word in enumerate(currsent):
                    env = get_env(k, currsent)
                    envvec = np.zeros((len(words_list),))
                    for l in env:
                        onevec = index_to_one_hot(l, words_list)
                        envvec = np.add(envvec, onevec)
                    # envvec = np.add([index_to_one_hot(l, words_list) for l in env])
                    # print('running')
                    _, currloss = sess.run([opt, loss], feed_dict = {onehots: envvec.reshape(1, len(words_list)), yt: [word]})
                    # print(currloss)
        embeds = sess.run(Win)

    embed_dict = {}
    for i, embed in enumerate(embeds):
        embed_dict[words_list[i]] = embed

    file = open(savepath,'wb')
    pickle.dump(embed_dict,file)
    file.close()

    return embed_dict

def word2vec_form_path(trainpath, savepath, embed_dim = EMBED_DIM, iternum = ITERNUM, lr = LR):
    # takes a **path of train data** (in the form of train.json) and hyper-parameters
    # returns a dictionary of words and their embeddings
    # and saving that dictionary to a pickle file "word_embeddings"
    # params:
    #   trainpath - the path
    #   savepath - a path to save the pickle file
    #   embed_dim - dimension of the embeddings. default: 8
    #   iternum - number of iterations over the training set. default: 3
    #   lr - learning rate of the SGD. default: 0.1

    data = read_data(trainpath)
    sents = []
    for datum in data:
        if datum['sentence'] not in sents:
            sents.append(datum['sentence'])
    embed_dict = word2vec(sents, savepath, embed_dim = EMBED_DIM, iternum = ITERNUM, lr = LR)
    return embed_dict

if __name__=='__main__':
    train = definitions.TRAIN_JSON
    data = read_data(train)
    samples, sents_dict = build_data(data, preprocessing_type='deep')
    sents_to_parse = sents_dict.values()
    embed_dict = word2vec(sents_to_parse, WORD_EMBEDDINGS_PATH)
