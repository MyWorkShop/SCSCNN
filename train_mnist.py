from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys
import tempfile
import time

from tensorflow.examples.tutorials.mnist import input_data

import tensorflow as tf

FLAGS = None

# Small CNN:
# convolution fliter of SCSCN


def small_cnn(x, num_conv, id, j, k):
    with tf.variable_scope('conv1'):
        W_conv1 = weight_variable_(
            [5,
             5,
             x.get_shape().as_list()[3],
             num_conv],
            id, j, k)
        b_conv1 = bias_variable_([num_conv], id, j, k)
        h_conv1 = tf.nn.relu(conv2d_(x, W_conv1) + b_conv1)

    with tf.variable_scope('conv2'):
        W_conv2 = weight_variable_(
            [5,
             5,
             num_conv,
             num_conv * 2],
            id, j, k)
        b_conv2 = bias_variable_([num_conv * 2], id, j, k)
        h_conv2 = tf.nn.relu(conv2d_(h_conv1, W_conv2) + b_conv2)

    with tf.variable_scope('conv3'):
        W_conv3 = weight_variable_(
            [5,
             5,
             num_conv * 2,
             num_conv * 4],
            id, j, k)
        b_conv3 = bias_variable_([num_conv * 4], id, j, k)
        h_conv3 = tf.nn.relu(conv2d_(h_conv2, W_conv3) + b_conv3)

    with tf.variable_scope('conv4'):
        W_conv4 = weight_variable_(
            [4,
             4,
             num_conv * 4,
             num_conv],
            id, j, k)
        b_conv4 = bias_variable_([num_conv], id, j, k)
        h_conv4 = tf.nn.relu(conv2d_(h_conv3, W_conv4) + b_conv4)
        y_conv = tf.reshape(h_conv4, [-1, num_conv])

    return y_conv


def deepnn(x):
    with tf.name_scope('reshape'):
        x_image = tf.reshape(x, [-1, 28, 28, 1])

    with tf.name_scope('SCSCN'):
        h_scscn = scscn(x_image, 1, 32)

    with tf.variable_scope('conv1'):
        W_conv1 = weight_variable([5, 5, 32, 64])
        b_conv1 = bias_variable([64])
        h_conv1 = tf.nn.relu(conv2d(h_scscn, W_conv1) + b_conv1)
        h_pool1_flat = tf.reshape(h_conv1, [-1, 7 * 7 * 64])

    # with tf.variable_scope('conv1'):
    #     W_conv1 = weight_variable([5, 5, 32, 64])
    #     b_conv1 = bias_variable([64])
    #     h_conv1 = tf.nn.relu(conv2d(h_scscn, W_conv1) + b_conv1)
    #
    # with tf.variable_scope('pool1'):
    #     h_pool1 = max_pool(h_conv1, 2, 2)
    #     h_pool1_flat = tf.reshape(h_pool1, [-1, 7 * 7 * 64])

    with tf.name_scope('fc1'):
        W_fc1 = weight_variable([7 * 7 * 64, 1024])
        b_fc1 = bias_variable([1024])
        h_fc1 = tf.matmul(h_pool1_flat, W_fc1) + b_fc1

    with tf.name_scope('dropout'):
        keep_prob = tf.placeholder(tf.float32)
        h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

    with tf.name_scope('fc2'):
        W_fc2 = weight_variable([1024, 10])
        b_fc2 = bias_variable([10])
        y_conv = tf.matmul(h_fc1_drop, W_fc2) + b_fc2
    return y_conv, keep_prob


def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def conv2d_(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')


def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1], padding='SAME')


def avg_pool(x, m, n):
    return tf.nn.avg_pool(x, ksize=[1, m, n, 1],
                          strides=[1, m, n, 1], padding='SAME')

def max_pool(x, m, n):
    return tf.nn.max_pool(x, ksize=[1, m, n, 1],
                          strides=[1, m, n, 1], padding='SAME')

def scscn(x, num, num_conv):
    with tf.name_scope('kernal_size'):
        # Kernal size:
        a = 16
        b = 16

    with tf.name_scope('strides'):
        # Strides:
        stride = 4

    with tf.name_scope('pad'):
        # pad of input
        padd = 6
        x = tf.pad(x, [[0, 0], [padd, padd], [padd, padd], [0, 0]])

    with tf.name_scope('input_size'):
        # Size of input:
        input_num = x.get_shape().as_list()[3]
        input_m = x.get_shape().as_list()[1]
        input_n = x.get_shape().as_list()[2]
        print('[input|SCSCN]num %d,m %d,n %d' % (input_num, input_m, input_n))

    with tf.name_scope('size'):
        # Size:
        m = int((input_m - a) / stride + 1)
        n = int((input_n - b) / stride + 1)

    with tf.name_scope('output'):
        # Output:
        # a TensorArray of tensor used to storage the output of small_cnn
        output = tf.TensorArray('float32', num * m * n)
        # w_fc = []
        # b_fc = []

    with tf.name_scope('fliter'):
        for i in range(num):
            # print the init state
            # print('[init|SCSCN]i %d' % (i))
            # w_fc.append(weight_variable([3, 3, num_conv * 4, num_conv]))
            # b_fc.append(bias_variable([num_conv]))

            for l in range(m*n):
                # for k in range(n):
                j = int(l / n)
                k = int(l % n)
                # calculate the output of the convolution fliter
                output = output.write((i * m + j ) * n + k,
                            tf.identity(small_cnn(
                                    tf.slice(x, [0, j * stride, k * stride, 0],
                                        [-1, a, b, input_num]),
                                            num_conv, i, j, k)))
                                            # num_conv, i, j, k, w_fc[i], b_fc[i])))

    # return the concated and reshaped data of output
    for i in range(m):
        for j in range(n):
            for k in range(num):
                if (j == 0)and(k == 0)and(i == 0):
                    output_ = output.read((k * m + i ) * n + j)
                else:
                    output_ = tf.concat([output_,
                                    output.read((k * m + i ) * n + j )], 1)
    return tf.reshape(output_,
                      [-1, m, n, num * num_conv])


def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.01, shape=shape)
    return tf.Variable(initial)


def weight_variable_(shape, id, j, k):
    return tf.get_variable("weights" + str(id) + "a" + str(j) + "a" + str(k),
                           shape, None, tf.random_normal_initializer(0, 0.01))


def bias_variable_(shape, id, j, k):
    return tf.get_variable("biases" + str(id) + "a" + str(j) + "a" + str(k),
                           shape, None, tf.constant_initializer(0.01))


def main(_):
    # Read data from MNIST
    mnist = input_data.read_data_sets('MNIST_data', one_hot=True)
    # mnist = input_data.read_data_sets('MNIST_data', one_hot=True)

    # Placehoder of input and output
    x = tf.placeholder(tf.float32, [None, 784])

    y_ = tf.placeholder(tf.float32, [None, 10])

    # The main model
    y_conv, keep_prob = deepnn(x)

    with tf.name_scope('loss'):
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=y_,
                                                                logits=y_conv)
    cross_entropy = tf.reduce_mean(cross_entropy)

    with tf.name_scope('adam_optimizer'):
        train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

    with tf.name_scope('accuracy'):
        correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y_, 1))
        correct_prediction = tf.cast(correct_prediction, tf.float32)
        accuracy = tf.reduce_mean(correct_prediction)

    with tf.name_scope('config'):
        config = tf.ConfigProto(
            inter_op_parallelism_threads = 81,
            intra_op_parallelism_threads = 8
        )

    with tf.name_scope('graph'):
        graph_location = tempfile.mkdtemp()
        print('Saving graph to: %s' % graph_location)
        train_writer = tf.summary.FileWriter(graph_location)
        train_writer.add_graph(tf.get_default_graph())

    # Start to run
    with tf.Session(config=config) as sess:

        sess.run(tf.global_variables_initializer())
        t0 = time.clock()
        for i in range(1000000):
            # Get the data of next batch
            batch = mnist.train.next_batch(100)
            if i % 600 == 0:
                # Print the accuracy
                train_accuracy = 0
                for index in range(50):
                    accuracy_batch = mnist.test.next_batch(200)
                    train_accuracy += accuracy.eval(feed_dict={
                        x: accuracy_batch[0], y_: accuracy_batch[1], keep_prob: 1.0})
                print(
                    'step %g, training accuracy %g | speed: %g samples/s' %
                    (i / 600, train_accuracy / 50, 100 * 600 / (time.clock() - t0)))
                t0 = time.clock()
            # Train
            train_step.run(
                feed_dict={x: batch[0],
                           y_: batch[1],
                           keep_prob: 0.5})

        print('test accuracy %g' % accuracy.eval(feed_dict={
            x: mnist.test.images, y_: mnist.test.labels, keep_prob: 1.0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,
                        default='/tmp/tensorflow/mnist/input_data',
                        help='Directory for storing input data')
    FLAGS, unparsed = parser.parse_known_args()
    tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
