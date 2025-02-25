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

import torch

from trident import function, operation, util


class AdaptiveAvgPool2d(torch.nn.Module):
    def __init__(self, output_size):
        """
        Applies Adaptive Average Pooling 2D to an input.

        Args:
            output_size: the target output size.
        """
        super().__init__()

        self.output_size = output_size

    def forward(self, input):
        """
        Applies Adaptive Average Pooling 2D to an input.

        Args:
            input: an input (N, C, H, W) or (C, H, W)

        Returns:
            an output (N, C, T, T) or (C, T, T)
        """
        assert input.dim() == 3 or input.dim() == 4

        x = AdaptiveAvgPool2d.__view(input)
        y = operation.AdaptiveAvgPool2d.apply(x, self.output_size)

        return y if y.dim() == 4 else y.squeeze()

    @staticmethod
    def __shape(x):
        if x.dim() == 3:
            return 1, x.shape[0], x.shape[1], x.shape[2]
        else:
            return x.shape

    @staticmethod
    def __view(x):
        num_batches, num_channels, height, width = AdaptiveAvgPool2d.__shape(x)
        return x.view(num_batches, num_channels, height, width)


class BatchNorm1d(torch.nn.Module):
    def __init__(
        self,
        num_features,
        eps=1e-05,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
        device=None,
        dtype=None,
    ):
        """
        Applies Batch Normalization over a 2D or 3D inputs.

        Args:
            num_features: number of features
            eps: a value added to the denominator for numerical stability
            momentum: the value used for the running_mean and running_var computation.
            affine: a boolean value that when set to True, this module has learnable affine parameters.
            track_running_stats: a boolean value that when set to True, this module tracks
                the running mean and variance, and when set to False, this module does not track such statistics,
                and initializes the statistics as None.
        """
        super().__init__()

        self.eps = eps
        self.momentum = momentum
        self.track_running_stats = track_running_stats
        self.device = device
        self.dtype = dtype

        if affine:
            self.weight = torch.nn.Parameter(
                torch.empty(num_features, device=device, dtype=dtype).fill_(1)
            )
            self.bias = torch.nn.Parameter(
                torch.zeros(num_features, device=device, dtype=dtype)
            )
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

        if self.track_running_stats:
            self.running_mean = torch.zeros(num_features, device=device, dtype=dtype)
            self.running_var = torch.ones(num_features, device=device, dtype=dtype)
        else:
            self.register_parameter("running_mean", None)
            self.register_parameter("running_var", None)

    def forward(self, input):
        """
        Applies Batch Normalization to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        assert input.dim() == 2
        assert input.shape[0] > 1

        if self.track_running_stats:
            self.running_mean = input.mean(
                axis=0
            ) * self.momentum + self.running_mean * (1 - self.momentum)
            self.running_var = input.var(axis=0) * self.momentum + self.running_var * (
                1 - self.momentum
            )

        return operation.BatchNorm.apply(input, self.weight, self.bias, self.eps)


class Conv2d(torch.nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, bias=True):
        """
        Applies Convolution 2D to an input.

        Args:
            in_channels: number of channels in the input image
            out_channels: number of channels produced by the convolution
            kernel_size: size of the convolution kernel
            bias: If True, adds a learnable bias to the output.
        """
        super().__init__()

        self.in_channels = in_channels
        self.weight = torch.empty(
            out_channels,
            in_channels,
            kernel_size,
            kernel_size,
            device="cuda",
            dtype=torch.float,
        )
        self.bias = (
            torch.empty(out_channels, device="cuda", dtype=torch.float)
            if bias
            else None
        )

    def forward(self, input):
        """
        Applies Convolution 2D to an input.

        Args:
            input: an input (N, C, H, W) or (C, H, W)

        Returns:
            an output (N, C, R, C) or (C, R, C)
        """
        return operation.Conv2d.apply(input, self.weight, self.bias)


class Dropout(torch.nn.Module):
    def __init__(self, p=0.5):
        """
        Applies Dropout to an input.

        During training, randomly zeroes some of the elements of the input tensor with probability using samples from a
        Bernoulli distribution. Each channel will be zeroed out independently on every forward call.

        Args:
            p: probability of an element to be zeroed
        """
        super().__init__()

        self.p = p

    def forward(self, input):
        """
        Applies Dropout to an input.

        Args:
            input: an input can be of any shape

        Returns:
            an output is of the same shape as input
        """
        return (
            operation.Dropout.apply(input, self.p) if self.training else input.clone()
        )


class GELU(torch.nn.Module):
    def __init__(self):
        """
        Applies the Gaussian Error Linear Units to an input.
        """
        super().__init__()

    def forward(self, input):
        """
        Applies the Gaussian Error Linear Units to an input.

        Args:
            input: an input can be of any shape

        Returns:
            an output is of the same shape as input
        """
        return operation.GELU.apply(input)


class GroupNorm(torch.nn.Module):
    def __init__(
        self,
        num_groups,
        num_channels,
        eps=1e-05,
        affine=True,
        device=None,
        dtype=None,
    ):
        """
        Applies Group Normalization over a mini-batch of inputs as described in the paper Group Normalization.

        Args:
            num_groups: number of groups to separate the channels into
            num_channels: number of channels expected in input
            eps: a value added to the denominator for numerical stability
            affine: a boolean value that when set to True, this module has learnable per-channel affine
                    parameters initialized to ones (for weights) and zeros (for biases)
        """
        super().__init__()

        if num_channels % num_groups != 0:
            raise ValueError("num_channels must be divisible by num_groups")

        ctor_args = {"device": device, "dtype": dtype}
        self.num_groups = num_groups
        self.num_channels = num_channels
        self.eps = eps
        self.device = device
        self.dtype = dtype

        if affine:
            self.weight = torch.nn.Parameter(
                torch.empty(num_channels, **ctor_args).fill_(1)
            )
            self.bias = torch.nn.Parameter(torch.zeros(num_channels, **ctor_args))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

    def forward(self, input):
        """
        Applies Group Normalization to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        return function.group_norm(
            input, self.num_groups, self.weight, self.bias, self.eps
        )


class InstanceNorm1d(torch.nn.Module):
    def __init__(
        self,
        num_features,
        eps=1e-05,
        momentum=0.1,
        affine=False,
        track_running_stats=False,
        device=None,
        dtype=None,
    ):
        """
        Applies Instance Normalization to an input as described in the paper Instance Normalization: The Missing
        Ingredient for Fast Stylization.

        Args:
            num_features: C from an expected input of size (N, C, L) or (C, L)
            eps: a value added to the denominator for numerical stability
        """
        super().__init__()

        ctor_args = {"device": device, "dtype": dtype}
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats

        if self.affine:
            self.weight = torch.nn.Parameter(torch.empty(num_features, **ctor_args))
            self.bias = torch.nn.Parameter(torch.empty(num_features, **ctor_args))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

        if self.track_running_stats:
            self.register_buffer("running_mean", torch.empty(num_features, **ctor_args))
            self.register_buffer("running_var", torch.empty(num_features, **ctor_args))
        else:
            self.register_buffer("running_mean", None)
            self.register_buffer("running_var", None)

        self.reset_parameters()

    def forward(self, input):
        """
        Applies Instance Normalization to an input.

        Args:
            input: an input (N, C, L) or (C, L)

        Returns:
            an output with the same dimension and shape as an input
        """
        if input.dim() == 2:
            inp = input.view(1, input.shape[0], input.shape[1])
        else:
            inp = input

        out = function.instance_norm(
            inp,
            self.running_mean,
            self.running_var,
            self.weight,
            self.bias,
            not self.track_running_stats,
            self.momentum,
            self.eps,
        )

        return out.view(input.shape)

    def reset_parameters(self):
        if self.affine:
            util.fill(self.weight, 1)
            util.zero(self.bias)

        if self.track_running_stats:
            self.running_mean.zero_()
            self.running_var.fill_(1)


class InstanceNorm2d(torch.nn.Module):
    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=False,
        track_running_stats=False,
        device=None,
        dtype=None,
    ):
        """
        Applies Instance Normalization to an input as described in the paper Instance Normalization: The Missing
        Ingredient for Fast Stylization.

        Args:
            num_features: C from an expected input of size (N, C, H, W) or (C, H, W)
            eps: a value added to the denominator for numerical stability
        """
        super().__init__()

        ctor_args = {"device": device, "dtype": dtype}
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats

        if self.affine:
            self.weight = torch.nn.Parameter(torch.empty(num_features, **ctor_args))
            self.bias = torch.nn.Parameter(torch.empty(num_features, **ctor_args))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

        if self.track_running_stats:
            self.register_buffer("running_mean", torch.empty(num_features, **ctor_args))
            self.register_buffer("running_var", torch.empty(num_features, **ctor_args))
        else:
            self.register_buffer("running_mean", None)
            self.register_buffer("running_var", None)

        self.reset_parameters()

    def forward(self, input):
        """
        Applies Instance Normalization to an input.

        Args:
            input: an input (N, C, H, W) or (C, H, W)

        Returns:
            an output with the same dimension and shape as an input
        """
        if input.dim() == 4:
            inp = input.view(input.shape[0], input.shape[1], -1)
        else:
            inp = input

        out = function.instance_norm(
            inp,
            self.running_mean,
            self.running_var,
            self.weight,
            self.bias,
            not self.track_running_stats,
            self.momentum,
            self.eps,
        )

        return out.view(input.shape)

    def reset_parameters(self):
        if self.affine:
            util.fill(self.weight, 1)
            util.zero(self.bias)

        if self.track_running_stats:
            self.running_mean.zero_()
            self.running_var.fill_(1)


class LayerNorm(torch.nn.Module):
    def __init__(
        self,
        normalized_shape,
        eps=1e-05,
        elementwise_affine=True,
        device=None,
        dtype=None,
    ):
        """
        Applies Layer Normalization to an input as described in the paper Layer Normalization.

        Args:
            normalized_shape: input shape from an expected input of size
            elementwise_affine: a boolean value that when set to True, this module has learnable per-element affine
                                parameters initialized to ones (for weights) and zeros (for biases)
            eps: a value added to the denominator for numerical stability
            device: the desired device of returned tensor
            dtype: the desired data type of returned tensor
        """
        super().__init__()

        ctor_args = {"device": device, "dtype": dtype}
        self.normalized_shape = normalized_shape
        self.eps = eps
        self.device = device
        self.dtype = dtype

        if elementwise_affine:
            self.weight = torch.nn.Parameter(
                torch.empty(normalized_shape, **ctor_args).fill_(1)
            )
            self.bias = torch.nn.Parameter(torch.zeros(normalized_shape, **ctor_args))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

    def forward(self, input):
        """
        Applies Layer Normalization to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        return function.layer_norm(
            input, self.normalized_shape, self.weight, self.bias, self.eps
        )


class LeakyReLU(torch.nn.Module):
    def __init__(self, negative_slope=1e-2):
        """
        Applies Leaky ReLU to an input.

        Args:
            negative_slope: Controls the angle of the negative slope(which is used for negative input values)
        """
        super().__init__()

        self.negative_slope = negative_slope

    def forward(self, input):
        """
        Applies Leaky ReLU to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        return operation.LeakyReLU.apply(input, self.negative_slope)


class Linear(torch.nn.Module):
    def __init__(self, in_features, out_features, bias=True, activation=None):
        """
        Applies Linear Transformation to an input.

        Args:
            in_features: size of each input sample
            out_features: size of each output sample
            bias: If set to False, the layer will not learn an additive bias
            activation: activation function
        """
        super().__init__()

        self.weight = torch.nn.Parameter(
            torch.empty(out_features, in_features, device="cuda")
        )

        if bias:
            self.bias = torch.nn.Parameter(torch.empty(out_features, device="cuda"))
        else:
            self.register_parameter("bias", None)

        self.activation = activation

    def forward(self, input):
        """
        Applies Linear Transformation to an input.

        Args:
            input: an input (*, in_features)

        Returns:
            an output (*, out_features)
        """
        return function.linear(input, self.weight, self.bias, self.activation)


class MaxPool2d(torch.nn.Module):
    def __init__(self, kernel_size):
        """
        Applies Max Pooling 2D to an input.

        Args:
            kernel_size: the size of the window to take a max over
        """
        super().__init__()

        self.kernel_size = kernel_size

    def forward(self, input):
        """
        Applies Max Pooling 2D to an input.

        Args:
            input: an input (N, C, inp_height, inp_width)

        Returns:
            an output (N, C, out_height, out_width)
        """
        return operation.MaxPool2d.apply(input, self.kernel_size)


class ReLU(torch.nn.Module):
    def __init__(self):
        """
        Applies Leaky ReLU to an input.
        """
        super().__init__()

    def forward(self, input):
        """
        Applies Leaky ReLU to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        return operation.ReLU.apply(input)


class PReLU(torch.nn.Module):
    def __init__(self, num_parameters=1, init=0.25):
        """
        Applies PReLU to an input.

        Args:
            num_parameters: number of weight to learn
            init: the initial value of weight
        """
        super().__init__()

        self.weight = torch.nn.Parameter(
            torch.empty(num_parameters, device="cuda").fill_(init)
        )

    def forward(self, input):
        """
        Applies PReLU to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        return operation.PReLU.apply(input, self.weight)


class SiLU(torch.nn.Module):
    def __init__(self):
        """
        Applies the Sigmoid Linear Unit, element-wise to an input. The SiLU function is also known as the Swish.
        """
        super().__init__()

    def forward(self, input):
        """
        Applies the Sigmoid Linear Unit to an input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input
        """
        return operation.SiLU.apply(input)


class Softmax(torch.nn.Module):
    def __init__(self, dim=None):
        """
        Applies Softmax to an input rescaling them so that an output lie in the range [0,1] and sum to 1.

        Args:
            dim: A dimension along which Softmax will be computed (so every slice along dim will sum to 1)
        """
        super().__init__()

        self.dim = dim

    def forward(self, input):
        """
        Applies Softmax to input.

        Args:
            input: an input

        Returns:
            an output with the same dimension and shape as an input with values in the range [0, 1]
        """
        return operation.Softmax.apply(input, self.dim)
