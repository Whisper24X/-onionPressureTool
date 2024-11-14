#!/usr/bin/env python
# coding:utf-8
"""
Name : FpsListener.py
Author  :
Contect :
Time    : 2020/7/23 16:07
Desc:
"""
from abc import ABCMeta, abstractmethod

class IFpsListener_android13(object):

    @abstractmethod
    def report_fps_info_android13(self, fps_info):
        pass

