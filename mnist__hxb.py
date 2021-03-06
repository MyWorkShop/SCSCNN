from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Imports
import tensorflow as tf
import time


def small_cnn(x, phase_train, location_labels):
    # Convolutional Layer #1
    conv1 = tf.layers.conv2d(
        inputs=x,
        filters=32,
        kernel_size=[5, 5],
        padding="same",
        activation=tf.nn.relu)

    # Convolutional Layer #2
    conv2 = tf.layers.conv2d(
        inputs=conv1,
        filters=32,
        kernel_size=[5, 5],
        padding="same",
        activation=tf.nn.relu)

    # Pooling Layer #1
    pool1 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

    # Convolutional Layer #3 #4 and Pooling Layer #2
    conv3 = tf.layers.conv2d(
        inputs=pool1,
        filters=32,
        kernel_size=[3, 3],
        padding="same",
        activation=tf.nn.relu)
    conv4 = tf.layers.conv2d(
        inputs=conv3,
        filters=32,
        kernel_size=[3, 3],
        padding="same",
        activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(inputs=conv4, pool_size=[2, 2], strides=2)

    # Dense Layer
    pool2_flat = tf.layers.dropout(
        inputs=tf.reshape(pool2, [-1, 4 * 4 * 32]),
        rate=0.,
        training=phase_train)
    pool2_flat = tf.concat([pool2_flat, location_labels], 1)
    dense = tf.layers.dense(
        inputs=pool2_flat, units=1024, activation=tf.nn.relu)
    dropout = tf.layers.dropout(inputs=dense, rate=0.4, training=phase_train)

    # Logits Layer
    logits = tf.layers.dense(inputs=dropout, units=10)
    return tf.layers.dropout(inputs=logits, rate=0.4, training=phase_train)

def cnnic(x):
    phase_train = tf.placeholder(tf.bool)

    m = 5
    n = 5
    stride = 3
    x = tf.reshape(x, [-1, 28, 28, 1])

    #Input of CNNIC
    slicing = tf.TensorArray('float32', m * n)
    locations = []
    location_template = []
    import copy
    for i in range(0, m * n):
        location_template.append(0.)
    for j in range(m):
        for k in range(n):
            locations.append(copy.deepcopy(location_template))
            locations[-1][j * k] = 1.
            print('Location Update: {}'.format(locations))
            slicing = slicing.write(j * n + k,
                                    tf.slice(x, [0, j * stride, k * stride, 0],
                                             [-1, 16, 16, 1]))
    scn_input = tf.reshape(slicing.concat(), [-1, 16, 16, 1])
    slicing.close().mark_used()
    location_tensors = tf.constant(locations)
    location_tensors = tf.cond(
        phase_train, lambda: tf.tile(location_tensors, tf.constant([100, 1])),
        lambda: tf.tile(location_tensors, tf.constant([50, 1])))
    location_tensors = tf.reshape(location_tensors, [-1, m * n])

    scn_output_raw = small_cnn(scn_input, phase_train, location_tensors)
    scn_output = tf.reshape(scn_output_raw, [m * n, -1, 10])
    cnnic_output = tf.reduce_mean(scn_output, 0)

    return cnnic_output, phase_train


def main(unused_argv):
    mnist = tf.contrib.learn.datasets.load_dataset("mnist")

    input_data = tf.placeholder(tf.float32, [None, 784])
    output_data = tf.placeholder(tf.int64, [None])
    y_model, phase_train = cnnic(input_data)

    #Loss
    cross_entropy = tf.losses.sparse_softmax_cross_entropy(
        labels=output_data, logits=y_model)
    cross_entropy = tf.reduce_mean(cross_entropy)

    #Optimizer
    rate = tf.placeholder(tf.float32)
    train_step = tf.train.AdamOptimizer(rate).minimize(cross_entropy)

    #Accuracy
    correct_prediction = tf.equal(tf.argmax(y_model, 1), output_data)
    correct_prediction = tf.cast(correct_prediction, tf.float32)

    accuracy = tf.reduce_mean(correct_prediction)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        t0 = time.clock()
        rt = 1e-3
        for i in range(60001):
            # Get the data of next batch
            batch = mnist.train.next_batch(100)
            if (i % 600 == 0) and (i != 0):
                if i == 30000:
                    rt = 3e-4
                if i == 42000:
                    rt = 1e-4
                if i == 48000:
                    rt = 3e-5
                if i == 54000:
                    rt = 1e-5
                # Print the accuracy
                test_accuracy = 0
                test_accuracy_once = 0
                for index in range(200):
                    accuracy_batch = mnist.test.next_batch(50)
                    test_accuracy_once = sess.run(
                        accuracy,
                        feed_dict={
                            input_data: accuracy_batch[0],
                            output_data: accuracy_batch[1],
                            phase_train: False
                        })
                    test_accuracy += test_accuracy_once
                    test_accuracy_once = 0
                print('%g, %g, %g' % (i / 600, test_accuracy / 200,
                                      (time.clock() - t0)))
                t0 = time.clock()
            # Train
            _ = sess.run(
                train_step,
                feed_dict={
                    input_data: batch[0],
                    output_data: batch[1],
                    phase_train: True,
                    rate: rt
                })


if __name__ == "__main__":
    tf.app.run()
