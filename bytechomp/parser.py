from __future__ import annotations
from typing import Tuple, Generic, TypeVar, Iterable, Iterator
from dataclasses import is_dataclass
from collections import OrderedDict
from struct import Struct
import inspect

from bytechomp.byte_order import ByteOrder
from bytechomp.data_descriptor import (
    build_data_description,
    build_data_pattern,
    build_structure,
)

T = TypeVar("T")  # pylint: disable=invalid-name


class Parser(Generic[T]):
    """A bytes parser.

    Args:
        Generic (T): The dataclass type that defines the binary protocol.
    """

    def __init__(self, byte_order: ByteOrder = ByteOrder.NATIVE) -> None:
        self.__datatype: type | None = None
        self.__byte_order = byte_order
        self.__data_description: OrderedDict = OrderedDict()
        self.__data_pattern: str = ""
        self.__struct = Struct(self.__data_pattern)

    def build(self) -> Parser[T]:
        """Builds the parser with a tokenized description of the protocol defined by the type T.

        Returns:
            Parser: The allocated binary protocol reader.
        """
        # pylint: disable=no-member

        self.__datatype = self.__orig_class__.__args__[0]  # type: ignore

        if (
            not inspect.isclass(self.__datatype)
            or not is_dataclass(self.__datatype)
            or self.__datatype is None
        ):
            raise ValueError("generic datatype must be a dataclass")

        # verify that the datatype contains only known types
        self.__data_description = build_data_description(self.__datatype)
        # print(self.__data_description)

        # build struct parsing pattern from the description
        self.__data_pattern = self.__byte_order.to_pattern() + build_data_pattern(
            self.__data_description
        )
        # print(self.__data_pattern)

        # create struct from this pattern
        self.__struct = Struct(self.__data_pattern)
        # print(self.__struct.size)

        return self

    def parse(self, array: bytes) -> Tuple[T | None, bytes]:
        """Constructs the class T from the binary data collected in the internal buffer.

        Returns:
            Optional[T]: Instantiated class T if the provided array is sufficiently large,
                otherwise None.
            bytes: extra bytes unused to build the struct
        """
        if len(array) < self.__struct.size:
            return None, array
        #XXX: This creates copies of the bytes object
        struct_bytes = array[: self.__struct.size]
        extra_bytes = array[self.__struct.size :]
        return build_structure(
            list(self.__struct.unpack(struct_bytes)), self.__data_description
        ), extra_bytes 
