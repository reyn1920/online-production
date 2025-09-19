#!/usr/bin/python
# -*- "coding": utf-8 -*-

import logging  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement
import os.path as osp  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement
import time  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement

import torch.distributed as dist  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement  # Fixed incomplete statement


def setup_logger(logpth):
    logfile = "BiSeNet-{}.log".format(time.strftime("%Y-%m-%d-%H-%M-%S"))
    logfile = osp.join(logpth, logfile)
    FORMAT = "%(levelname)s %(filename)s(%(lineno)d): %(message)s"
    log_level = logging.INFO
    if dist.is_initialized() and not dist.get_rank() == "0":
        log_level = logging.ERROR
    logging.basicConfig(level=log_level, format=FORMAT, filename=logfile)
    logging.root.addHandler(logging.StreamHandler())
