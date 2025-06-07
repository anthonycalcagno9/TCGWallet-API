"""
TCGPlayer API client module for One Piece Card Game data.
This module provides typed interfaces and functions for accessing TCGPlayer API endpoints.
"""
from typing import Any, List, Optional, TypedDict


# Base response type
class TCGPlayerResponse(TypedDict):
    success: bool
    errors: List[str]
    totalItems: Optional[int]
    results: List[Any]


# Group types
class TCGPlayerGroup(TypedDict):
    groupId: int
    name: str
    abbreviation: str
    isSupplemental: bool
    publishedOn: str
    modifiedOn: str
    categoryId: int


class TCGPlayerGroupResponse(TCGPlayerResponse):
    results: List[TCGPlayerGroup]


# Product types
class PresaleInfo(TypedDict):
    isPresale: bool
    releasedOn: Optional[str]
    note: Optional[str]


class TCGPlayerProduct(TypedDict):
    productId: int
    name: str
    cleanName: str
    imageUrl: str
    categoryId: int
    groupId: int
    url: str
    modifiedOn: str
    imageCount: int
    presaleInfo: PresaleInfo
    extendedData: List[Any]


class TCGPlayerProductResponse(TCGPlayerResponse):
    results: List[TCGPlayerProduct]


# Price types
class TCGPlayerPrice(TypedDict):
    productId: int
    lowPrice: Optional[float]
    midPrice: Optional[float]
    highPrice: Optional[float]
    marketPrice: Optional[float]
    directLowPrice: Optional[float]
    subTypeName: str


class TCGPlayerPriceResponse(TCGPlayerResponse):
    results: List[TCGPlayerPrice]
