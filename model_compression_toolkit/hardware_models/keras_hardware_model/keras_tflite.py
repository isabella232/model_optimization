# Copyright 2022 Sony Semiconductors Israel, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import tensorflow as tf
from keras import layers
from keras.layers import Conv2D, Dense, Reshape, ZeroPadding2D, \
    MaxPooling2D, ReLU, AveragePooling2D, Activation, DepthwiseConv2D
from tensorflow.python.ops.image_ops_impl import ResizeMethod

from model_compression_toolkit.common.hardware_representation import FrameworkHardwareModel
from model_compression_toolkit.common.hardware_representation.hardware2framework import OperationsSetToLayers, \
    LayerFilterParams
from model_compression_toolkit.common.hardware_representation.hardware2framework.attribute_filter import Eq
from model_compression_toolkit.hardware_models.tflite import get_tflite_hw_model


def get_keras_hardware_model_tflite():
    tflite_hm = get_tflite_hw_model()
    tflite_keras = FrameworkHardwareModel(tflite_hm, name='tflite_keras')

    with tflite_keras:
        OperationsSetToLayers("PreserveQuantizationParams", [AveragePooling2D,
                                                             tf.nn.avg_pool2d,
                                                             layers.Concatenate,
                                                             tf.concat,
                                                             MaxPooling2D,
                                                             layers.Multiply,
                                                             tf.multiply,
                                                             Reshape,
                                                             tf.reshape,
                                                             LayerFilterParams(tf.image.resize,
                                                                               method=ResizeMethod.BILINEAR),
                                                             tf.nn.space_to_depth,
                                                             ZeroPadding2D,
                                                             tf.gather,
                                                             tf.compat.v1.batch_to_space_nd,
                                                             tf.space_to_batch_nd,
                                                             tf.transpose,
                                                             tf.maximum,
                                                             layers.Maximum,
                                                             tf.minimum,
                                                             layers.Minimum,
                                                             tf.pad,
                                                             tf.slice,
                                                             layers.SlicingOpLambda])

        OperationsSetToLayers("FullyConnected", [Dense])
        OperationsSetToLayers("L2Normalization", [tf.math.l2_normalize])
        OperationsSetToLayers("LogSoftmax", [tf.nn.log_softmax])
        OperationsSetToLayers("Tanh", [tf.nn.tanh,
                                       LayerFilterParams(Activation, activation="tanh")])

        OperationsSetToLayers("Softmax", [tf.nn.softmax,
                                          layers.Softmax,
                                          LayerFilterParams(Activation, activation="softmax")])

        OperationsSetToLayers("Logistic", [tf.sigmoid,
                                           LayerFilterParams(Activation, activation="sigmoid")])

        OperationsSetToLayers("Conv2d", [Conv2D])
        OperationsSetToLayers("DepthwiseConv2D", [DepthwiseConv2D])

        OperationsSetToLayers("Relu", [tf.nn.relu,
                                       tf.nn.relu6,
                                       LayerFilterParams(ReLU, Eq("max_value", None) | Eq("max_value", 6)),
                                       LayerFilterParams(Activation, activation="relu")])

        OperationsSetToLayers("Elu", [tf.nn.elu,
                                      LayerFilterParams(Activation, activation="elu")])

        OperationsSetToLayers("BatchNorm", [layers.BatchNormalization,
                                            tf.nn.batch_normalization])

        OperationsSetToLayers("Squeeze", [tf.squeeze])
        OperationsSetToLayers("BiasAdd", [tf.nn.bias_add])
        OperationsSetToLayers("Add", [tf.add,
                                      layers.Add])

    return tflite_keras


