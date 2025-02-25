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
import triton
import util

import trident


@util.report(
    "leaky relu forward",
    ["vec_sz"],
    [256 * i for i in range(1, 21)],
    {"num_vec": 64},
)
def bench_leaky_relu_forward(num_vec, vec_sz, ctx):
    inp = torch.randn(num_vec, vec_sz, device="cuda")

    if ctx == "torch":
        return triton.testing.do_bench(lambda: torch.nn.functional.leaky_relu(inp))
    else:
        return triton.testing.do_bench(lambda: trident.function.leaky_relu(inp))


def run_benchmark(mode, show_plots):
    if mode == "forward":
        bench_leaky_relu_forward.run(print_data=True, show_plots=show_plots)
    else:
        raise NotImplementedError("The backward isn't implemented.")
