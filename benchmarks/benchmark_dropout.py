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

import trident


@triton.testing.perf_report(
    triton.testing.Benchmark(
        x_names=['inp_sz'],
        x_vals=[2 ** i for i in range(8, 30, 2)],
        line_arg='provider',
        line_vals=['torch', 'trident'],
        line_names=['torch', 'trident'],
        plot_name='dropout forward',
        args={'p': 0.5},
        ylabel='milliseconds',
        x_log=True
    )
)
def bench_dropout_forward(p, inp_sz, provider):
    inp = torch.randn(inp_sz, device='cuda')

    if provider == 'torch':
        return triton.testing.do_bench(lambda: torch.nn.functional.dropout(inp, p))
    else:
        return triton.testing.do_bench(lambda: trident.function.dropout(inp, p))


def run_benchmarks(show_plots):
    bench_dropout_forward.run(print_data=True, show_plots=show_plots)
