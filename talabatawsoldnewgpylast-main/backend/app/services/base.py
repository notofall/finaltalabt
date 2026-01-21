"""
Base Service Interface
كل الـ services ترث من هذا الـ interface
"""
from abc import ABC
from typing import Generic, TypeVar

T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """Base service interface"""
    pass
