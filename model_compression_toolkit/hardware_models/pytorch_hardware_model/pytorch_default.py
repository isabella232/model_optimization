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

import operator

import torch
from torch import add, flatten, reshape, split, unsqueeze, dropout, sigmoid, tanh
from torch.nn import Conv2d, ConvTranspose2d, Linear, BatchNorm2d
from torch.nn import Dropout, Flatten, Hardtanh
from torch.nn import ReLU, ReLU6, PReLU, SiLU, Sigmoid, Tanh
from torch.nn.functional import relu, relu6, prelu, silu, hardtanh

from model_compression_toolkit.common.hardware_representation.hardware2framework import \
    FrameworkHardwareModel, LayerFilterParams
from model_compression_toolkit.common.hardware_representation.hardware2framework import \
    OperationsSetToLayers
from model_compression_toolkit.hardware_models.default_hwm import get_default_hardware_model


def get_default_hwm_pytorch():
    default_hm = get_default_hardware_model()
    default_hwm_pytorch = FrameworkHardwareModel(default_hm,
                                                 name='default_hwm_pytorch')

    with default_hwm_pytorch:
        OperationsSetToLayers("NoQuantization", [Dropout,
                                                 Flatten,
                                                 dropout,
                                                 flatten,
                                                 split,
                                                 operator.getitem,
                                                 reshape,
                                                 unsqueeze,
                                                 BatchNorm2d])

        OperationsSetToLayers("Conv", [Conv2d])

        OperationsSetToLayers("FullyConnected", [Linear])

        OperationsSetToLayers("ConvTranspose", [ConvTranspose2d])

        OperationsSetToLayers("AnyReLU", [torch.relu,
                                          ReLU,
                                          ReLU6,
                                          relu,
                                          relu6,
                                          LayerFilterParams(Hardtanh, min_val=0),
                                          LayerFilterParams(hardtanh, min_val=0)])

        OperationsSetToLayers("Add", [operator.add,
                                      add])

        OperationsSetToLayers("PReLU", [PReLU,
                                        prelu])

        OperationsSetToLayers("Swish", [SiLU,
                                        silu])

        OperationsSetToLayers("Sigmoid", [Sigmoid,
                                          sigmoid])

        OperationsSetToLayers("Tanh", [Tanh,
                                       tanh])

    return default_hwm_pytorch



