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

from typing import Callable, List

from model_compression_toolkit import common
from model_compression_toolkit.common import Logger
from model_compression_toolkit.common.constants import TENSORFLOW
from model_compression_toolkit.common.gptq.gptq_config import GradientPTQConfig
from model_compression_toolkit.common.mixed_precision.kpi import KPI
from model_compression_toolkit.common.framework_info import FrameworkInfo
from model_compression_toolkit.common.network_editors.actions import EditRule
from model_compression_toolkit.common.mixed_precision.mixed_precision_quantization_config import \
    MixedPrecisionQuantizationConfig, DEFAULT_MIXEDPRECISION_CONFIG
from model_compression_toolkit.common.post_training_quantization import post_training_quantization
from model_compression_toolkit.common.quantization.quantization_config import QuantizationConfig
from model_compression_toolkit.common.quantization.quantization_config import DEFAULTCONFIG

import importlib

from model_compression_toolkit.common.hardware_representation.hardware2framework import FrameworkHardwareModel


if importlib.util.find_spec("tensorflow") is not None\
        and importlib.util.find_spec("tensorflow_model_optimization") is not None:
    import tensorflow as tf
    from model_compression_toolkit.keras.default_framework_info import DEFAULT_KERAS_INFO
    from model_compression_toolkit.keras.keras_implementation import KerasImplementation
    from model_compression_toolkit.keras.keras_model_validation import KerasModelValidation
    from tensorflow.keras.models import Model
    from model_compression_toolkit.keras.gradient_ptq.gptq_loss import multiple_tensors_mse_loss
    from keras.optimizer_v2.optimizer_v2 import OptimizerV2
    from model_compression_toolkit.keras.constants import DEFAULT_HWM

    from model_compression_toolkit import get_model
    KERAS_DEFAULT_MODEL = get_model(TENSORFLOW, DEFAULT_HWM)

    def get_keras_gptq_config(n_iter: int,
                              optimizer: OptimizerV2 = tf.keras.optimizers.Adam(),
                              loss: Callable = multiple_tensors_mse_loss,
                              log_function: Callable = None,
                              train_bias: bool = True):
        """
        Create a GradientPTQConfig instance for Keras models.

        args:
            n_iter (int): Number of iterations to fine-tune.
            optimizer (OptimizerV2): Keras optimizer to use for fine-tuning.
            loss (Callable): loss to use during fine-tuning. should accept 4 lists of tensors. 1st list of quantized tensors, the 2nd list is the float tensors,
             the 3rd is a list of quantized weights and the 4th is a list of float weights.
            log_function (Callable): Function to log information about the gptq process.
            train_bias (bool): Whether to update the bias during the the fine-tuning or not.

        returns:
            a GradientPTQConfig object to use when fine-tuning the quantized model using gptq.

        examples:
            Create a GradientPTQConfig to run for 5 iteration:

            >>> gptq_conf = get_keras_gptq_config(n_iter=5)

            To disable the biases training, one may set train_bias to false (enabled by default):

            >>> gptq_conf = get_keras_gptq_config(n_iter=5, train_bias=false)

            Other Tensorflow optimizers can be passed:

            >>> gptq_conf = get_keras_gptq_config(n_iter=3, optimizer=tf.keras.optimizers.Nadam())

            The configuration can be passed to :func:`~model_compression_toolkit.keras_post_training_quantization` in order to quantize a keras model using gptq.

        """

        return GradientPTQConfig(n_iter,
                                 optimizer,
                                 loss=loss,
                                 log_function=log_function,
                                 train_bias=train_bias)

    def keras_post_training_quantization(in_model: Model,
                                         representative_data_gen: Callable,
                                         n_iter: int = 500,
                                         quant_config: QuantizationConfig = DEFAULTCONFIG,
                                         fw_info: FrameworkInfo = DEFAULT_KERAS_INFO,
                                         network_editor: List[EditRule] = [],
                                         gptq_config: GradientPTQConfig = None,
                                         analyze_similarity: bool = False,
                                         fw_hw_model: FrameworkHardwareModel = KERAS_DEFAULT_MODEL):
        """
        Quantize a trained Keras model using post-training quantization. The model is quantized using a
        symmetric constraint quantization thresholds (power of two).
        The model is first optimized using several transformations (e.g. BatchNormalization folding to
        preceding layers). Then, using a given dataset, statistics (e.g. min/max, histogram, etc.) are
        being collected for each layer's output (and input, depends on the quantization configuration).
        Thresholds are then being calculated using the collected statistics and the model is quantized
        (both coefficients and activations by default).
        If a gptq configuration is passed, the quantized weights are optimized using gradient based post
        training quantization by comparing points between the float and quantized models, and minimizing the observed loss.

        Args:
            in_model (Model): Keras model to quantize.
            representative_data_gen (Callable): Dataset used for calibration.
            n_iter (int): Number of calibration iterations to run.
            quant_config (QuantizationConfig): QuantizationConfig containing parameters of how the model should be quantized. `Default configuration. <https://github.com/sony/model_optimization/blob/21e21c95ca25a31874a5be7af9dd2dd5da8f3a10/model_compression_toolkit/common/quantization/quantization_config.py#L154>`_
            fw_info (FrameworkInfo): Information needed for quantization about the specific framework (e.g., kernel channels indices, groups of layers by how they should be quantized, etc.). `Default Keras info <https://github.com/sony/model_optimization/blob/21e21c95ca25a31874a5be7af9dd2dd5da8f3a10/model_compression_toolkit/keras/default_framework_info.py#L113>`_
            network_editor (List[EditRule]): List of EditRules. Each EditRule consists of a node filter and an action to change quantization settings of the filtered nodes.
            gptq_config (GradientPTQConfig): Configuration for using gptq (e.g. optimizer).
            analyze_similarity (bool): Whether to plot similarity figures within TensorBoard (when logger is enabled) or not.
            fw_hw_model (FrameworkHardwareModel): FrameworkHardwareModel to optimize the Keras model according to.

        Returns:
            A quantized model and information the user may need to handle the quantized model.

        Examples:
            Import a Keras model:

            >>> from tensorflow.keras.applications.mobilenet import MobileNet
            >>> model = MobileNet()

            Create a random dataset generator:

            >>> import numpy as np
            >>> def repr_datagen(): return [np.random.random((1,224,224,3))]

            Import mct and pass the model with the representative dataset generator to get a quantized model:

            >>> import model_compression_toolkit as mct
            >>> quantized_model, quantization_info = mct.keras_post_training_quantization(model, repr_datagen, n_iter=1)

        """
        KerasModelValidation(model=in_model,
                             fw_info=fw_info).validate()
        return post_training_quantization(in_model,
                                          representative_data_gen,
                                          n_iter,
                                          quant_config,
                                          fw_info,
                                          KerasImplementation(),
                                          fw_hw_model,
                                          network_editor,
                                          gptq_config,
                                          analyze_similarity)


    def keras_post_training_quantization_mixed_precision(in_model: Model,
                                                         representative_data_gen: Callable,
                                                         n_iter: int = 500,
                                                         quant_config: MixedPrecisionQuantizationConfig = DEFAULT_MIXEDPRECISION_CONFIG,
                                                         fw_info: FrameworkInfo = DEFAULT_KERAS_INFO,
                                                         network_editor: List[EditRule] = [],
                                                         gptq_config: GradientPTQConfig = None,
                                                         analyze_similarity: bool = False,
                                                         target_kpi: KPI = None,
                                                         fw_hw_model: FrameworkHardwareModel = KERAS_DEFAULT_MODEL):
        """
         Quantize a trained Keras model using post-training quantization. The model is quantized using a
         symmetric constraint quantization thresholds (power of two).
         The model is first optimized using several transformations (e.g. BatchNormalization folding to
         preceding layers). Then, using a given dataset, statistics (e.g. min/max, histogram, etc.) are
         being collected for each layer's output (and input, depends on the quantization configuration).
         For each possible bit width (per layer) a threshold is then being calculated using the collected
         statistics. Then, using an ILP solver we find a mixed-precision configuration, and set a bit width
         for each layer. The model is then quantized (both coefficients and activations by default).
         In order to limit the maximal model's size, a target KPI can be passed after weights_memory
         is set (in bytes).
         If a gptq configuration is passed, the quantized weights are optimized using gradient based post
         training quantization by comparing points between the float and quantized models, and minimizing the observed loss.
         Notice that this feature is experimental.
         **For now, mixed precision is supported for weights only.**

         Args:
             in_model (Model): Keras model to quantize.
             representative_data_gen (Callable): Dataset used for calibration.
             n_iter (int): Number of calibration iterations to run.
             quant_config (MixedPrecisionQuantizationConfig): QuantizationConfig containing parameters of how the model should be quantized.
             fw_info (FrameworkInfo): Information needed for quantization about the specific framework (e.g., kernel channels indices, groups of layers by how they should be quantized, etc.). `Default Keras info <https://github.com/sony/model_optimization/blob/main/model_compression_toolkit/keras/default_framework_info.py#L100>`_
             network_editor (List[EditRule]): List of EditRules. Each EditRule consists of a node filter and an action to change quantization settings of the filtered nodes.
             gptq_config (GradientPTQConfig): Configuration for using GPTQ (e.g. optimizer).
             analyze_similarity (bool): Whether to plot similarity figures within TensorBoard (when logger is enabled) or not.
             target_kpi (KPI): KPI object to limit the search of the mixed-precision configuration as desired.
             fw_hw_model (FrameworkHardwareModel): FrameworkHardwareModel to optimize the Keras model according to.


         Returns:
             A quantized model and information the user may need to handle the quantized model.

         Examples:
             Import MCT:

             >>> import model_compression_toolkit as mct

             Import a Keras model:

             >>> from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
             >>> model = MobileNetV2()

             Create a random dataset generator:

             >>> import numpy as np
             >>> def repr_datagen(): return [np.random.random((1,224,224,3))]

             Create a mixed-precision configuration, to quantize a model with different bitwidths for different layers.
             Here, each layer can be quantized by 2, 4 or 8 bits:

             >>> config = mct.MixedPrecisionQuantizationConfig(weights_n_bits=[4, 2, 8])

             Create a KPI object to limit our returned model's size. Note that this value affects only coefficients that should be quantized (for example, the kernel of Conv2D in Keras will be affected by this value, while the bias will not):

             >>> kpi = mct.KPI(model.count_params() * 0.75)  # About 0.75 of the model size when quantized with 8 bits.

             Pass the model, the representative dataset generator, the configuration and the target KPI to get a quantized model:

             >>> quantized_model, quantization_info = mct.keras_post_training_quantization_mixed_precision(model, repr_datagen, n_iter=10, quant_config=config, target_kpi=kpi)

             For more configuration options, please take a look at our `API documentation <https://sony.github.io/model_optimization/api/api_docs/modules/mixed_precision_quantization_config.html>`_.

         """
        KerasModelValidation(model=in_model,
                             fw_info=fw_info).validate()

        if target_kpi is None:
            common.Logger.warning("No KPI was passed. Using non mixed-precision compression process...")
            # Before starting non-mixed-precision process, we need to set only single bit width, so we take the best
            # option which is the maximal number of bits.
            quant_config.weights_n_bits = [max(quant_config.weights_n_bits)]
            return keras_post_training_quantization(in_model,
                                                    representative_data_gen,
                                                    n_iter,
                                                    quant_config,
                                                    fw_info,
                                                    network_editor,
                                                    gptq_config,
                                                    analyze_similarity,
                                                    fw_hw_model)

        common.Logger.info("Using experimental mixed-precision quantization. "
                           "If you encounter an issue please file a bug.")

        return post_training_quantization(in_model,
                                          representative_data_gen,
                                          n_iter,
                                          quant_config,
                                          fw_info,
                                          KerasImplementation(),
                                          fw_hw_model,
                                          network_editor,
                                          gptq_config,
                                          analyze_similarity,
                                          target_kpi)

else:
    # If tensorflow or tensorflow_model_optimization are not installed,
    # we raise an exception when trying to use these functions.
    def keras_post_training_quantization(*args, **kwargs):
        Logger.critical('Installing tensorflow and tensorflow_model_optimization is mandatory '
                        'when using keras_post_training_quantization. '
                        'Could not find Tensorflow package.')

    def keras_post_training_quantization_mixed_precision(*args, **kwargs):
        Logger.critical('Installing tensorflow and tensorflow_model_optimization is mandatory '
                        'when using keras_post_training_quantization_mixed_precision. '
                        'Could not find Tensorflow package.')

    def get_keras_gptq_config(*args, **kwargs):
        Logger.critical('Installing tensorflow and tensorflow_model_optimization is mandatory '
                        'when using keras_post_training_quantization_mixed_precision. '
                        'Could not find Tensorflow package.')

