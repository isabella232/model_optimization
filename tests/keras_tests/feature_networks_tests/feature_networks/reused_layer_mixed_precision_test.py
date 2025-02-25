# Copyright 2021 Sony Semiconductors Israel, Inc. All rights reserved.
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
from model_compression_toolkit.common.mixed_precision.kpi import KPI
from model_compression_toolkit.common.mixed_precision.mixed_precision_quantization_config import \
    MixedPrecisionQuantizationConfig
from tests.common_tests.base_feature_test import BaseFeatureNetworkTest
import model_compression_toolkit as mct
import tensorflow as tf
from tests.keras_tests.feature_networks_tests.base_keras_feature_test import BaseKerasFeatureNetworkTest
import numpy as np
from tests.common_tests.helpers.tensors_compare import cosine_similarity

keras = tf.keras
layers = keras.layers


class ReusedLayerMixedPrecisionTest(BaseKerasFeatureNetworkTest):
    def __init__(self, unit_test):
        super().__init__(unit_test)

    def get_quantization_config(self):
        qc = mct.QuantizationConfig(mct.QuantizationErrorMethod.MSE, mct.QuantizationErrorMethod.MSE,
                                    activation_n_bits=16, relu_bound_to_power_of_2=True, weights_bias_correction=True,
                                    weights_per_channel_threshold=True, input_scaling=True,
                                    activation_channel_equalization=True)

        return MixedPrecisionQuantizationConfig(qc, weights_n_bits=[2, 16, 4])

    def create_networks(self):
        layer = layers.Conv2D(3, 4)
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layer(inputs)
        x = layer(x)
        model = keras.Model(inputs=inputs, outputs=x)
        return model

    def get_kpi(self):
        return KPI(np.inf)

    def compare(self, quantized_model, float_model, input_x=None, quantization_info=None):
        if isinstance(float_model.layers[1], layers.Conv2D):
            self.unit_test.assertTrue(isinstance(quantized_model.layers[2], layers.Conv2D))
            self.unit_test.assertFalse(hasattr(quantized_model.layers[2], 'input_shape'))  # assert it's reused
        if isinstance(float_model.layers[1], layers.SeparableConv2D):
            self.unit_test.assertTrue(isinstance(quantized_model.layers[2], layers.DepthwiseConv2D))
            self.unit_test.assertFalse(hasattr(quantized_model.layers[2], 'input_shape'))  # assert it's reused
            self.unit_test.assertTrue(isinstance(quantized_model.layers[4], layers.Conv2D))
            self.unit_test.assertFalse(hasattr(quantized_model.layers[4], 'input_shape'))  # assert it's reused


class ReusedSeparableMixedPrecisionTest(ReusedLayerMixedPrecisionTest):

    def __init__(self, unit_test):
        super().__init__(unit_test)

    def create_networks(self):
        layer = layers.SeparableConv2D(3, 3)
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layer(inputs)
        x = layer(x)
        model = keras.Model(inputs=inputs, outputs=x)
        return model
