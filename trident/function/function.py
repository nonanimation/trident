# Copyright 2023 ⓒ Kakao Brain Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from trident import operation


def adaptive_avg_pool2d(input, output_size):
    """
    Applies Adaptive Average Pooling 2D to an input.

    See AdaptiveAvgPool2d for details.
    """
    return operation.AdaptiveAvgPool2d.apply(input, output_size)


def batch_norm(input, running_mean=None, running_var=None, eps=1e-05, training=False):
    """
    Applies Batch Normalization for last certain number of dimensions.

    See BatchNorm for details.
    """
    if training:
        running_mean, running_var = None, None
    else:
        assert running_mean is not None and running_var is not None

    return operation.BatchNorm.apply(input, None, None, eps, running_mean, running_var)


def conv2d(input, weight, bias=None):
    """
    Applies Convolution 2D to an input.

    See Conv2d for details.
    """
    return operation.Conv2d.apply(input, weight, bias)


def dropout(input, p=0.5, training=True):
    """
    Applies Dropout to an input.

    See Dropout for details.
    """
    return operation.Dropout.apply(input, p) if training else input.clone()


def gelu(input, approximate="none"):
    """
    Applies the Gaussian Error Linear Units to an input.

    See GELU for details.
    """
    return operation.GELU.apply(input)


def group_norm(input, num_groups, weight=None, bias=None, eps=1e-05):
    """
    Applies Group Normalization for last certain number of dimensions.

    See GroupNorm for details.
    """
    return operation.GroupNorm.apply(input, num_groups, weight, bias, eps)


def instance_norm(
    input,
    running_mean=None,
    running_var=None,
    weight=None,
    bias=None,
    use_input_stats=True,
    momentum=0.1,
    eps=1e-05,
):
    """
    Applies Instance Normalization for each channel in each data sample in a batch.

    See InstanceNorm2d for details.
    """
    return operation.InstanceNorm.apply(
        input,
        running_mean,
        running_var,
        weight,
        bias,
        use_input_stats,
        momentum,
        eps,
    )


def layer_norm(input, normalized_shape, weight=None, bias=None, eps=1e-05):
    """
    Applies Layer Normalization for last certain number of dimensions.

    See LayerNorm for details.
    """
    return operation.LayerNorm.apply(input, normalized_shape, weight, bias, eps)


def leaky_relu(input, negative_slope=0.01):
    """
    Applies Leaky ReLU to an input.

    See LeakyReLU for more details.
    """
    return operation.LeakyReLU.apply(input, negative_slope)


def linear(input, weight, bias=None, activation=""):
    """
    Applies Linear Transformation to an input.

    See Linear for more details.
    """
    return operation.Linear.apply(input, weight, bias, activation)


def max_pool2d(input, kernel_size):
    """
    Applies Max Pooling 2D to an input.

    See MaxPool2d for details.
    """
    return operation.MaxPool2d.apply(input, kernel_size)


def relu(input):
    """
    Applies ReLU to an input.

    See ReLU for more details.
    """
    return operation.ReLU.apply(input)


def silu(input):
    """
    Applies the Sigmoid Linear Unit to an input.

    See SiLU for more details.
    """
    return operation.SiLU.apply(input)


def prelu(input, weight):
    """
    Applies PReLU to an input.

    See PReLU for more details.
    """
    return operation.PReLU.apply(input, weight)


def softmax(input, dim=None):
    """
    Applies Softmax to an input rescaling them so that an output lie in the range [0,1] and sum to 1.

    See Softmax for more details.
    """
    return operation.Softmax.apply(input, dim)
