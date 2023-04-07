"""
Copyright ⓒ Kakao Brain Corp. All rights reserved.

Unauthorized copying of this file, via any medium is strictly prohibited.
Proprietary and confidential.
"""

import triton
import triton.language as tl

from .activation import *

def get_configs_linear_io_bound():
    configs = []
    for num_stages in [2, 3]:
        for block_size_m in [64, 128, 256]:
            for block_size_n in [64, 128, 256]:
                num_warps = 2 if block_size_n <= 64 else 4
                configs.append(triton.Config({'BLOCK_SIZE_M': block_size_m, 'BLOCK_SIZE_N': block_size_n},
                                             num_stages=num_stages, num_warps=num_warps))
    return configs


@triton.autotune(
    configs=get_configs_linear_io_bound(),
    key=['size_m', 'size_n']
)
@triton.jit
def linear(x_ptr, stride_x_m, stride_x_k,
           y_ptr, stride_y_m, stride_y_n,
           w_ptr, stride_w_n, stride_w_k,
           b_ptr, stride_b_n,
           size_m, size_k, size_n,
           ACTIVATION: tl.constexpr,
           BLOCK_SIZE_M: tl.constexpr, BLOCK_SIZE_K: tl.constexpr, BLOCK_SIZE_N: tl.constexpr):
    i = tl.program_id(0)
    j = tl.program_id(1)

    range_m = tl.arange(0, BLOCK_SIZE_M) + i * BLOCK_SIZE_M
    range_k = tl.arange(0, BLOCK_SIZE_K)
    range_n = tl.arange(0, BLOCK_SIZE_N) + j * BLOCK_SIZE_N

    total = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)

    x_ptr += range_m[:, None] * stride_x_m + range_k[None, :] * stride_x_k
    w_ptr += range_n[:, None] * stride_w_n + range_k[None, :] * stride_w_k

    for k in range(0, size_k, BLOCK_SIZE_K):
        mask_m = range_m[:, None] < size_m
        mask_k = range_k[None, :] + k < size_k
        mask_n = range_n[:, None] < size_n

        x = tl.load(x_ptr, mask_m & mask_k, 0.0)
        w = tl.load(w_ptr, mask_n & mask_k, 0.0)
        total += tl.dot(x, tl.trans(w))

        x_ptr += BLOCK_SIZE_K * stride_x_k
        w_ptr += BLOCK_SIZE_K * stride_w_k

    if b_ptr is not None:
        b_ptr += range_n * stride_b_n
        mask_n = range_n < size_n
        b = tl.load(b_ptr, mask_n, 0.0)
        total += b[None, :]

    if ACTIVATION == 'relu':
        total = relu(total)

    y_ptr += range_m[:, None] * stride_y_m + range_n[None, :] * stride_y_n
    mask_m = range_m[:, None] < size_m
    mask_n = range_n[None, :] < size_n
    tl.store(y_ptr, total, mask_m & mask_n)


