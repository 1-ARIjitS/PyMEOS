from __future__ import annotations

from typing import Optional, Union, List

from pymeos_cffi import *
from spans import intrange, floatrange

from ..main import TNumber
from ..time import *


class TBox:
    """
    Class for representing numeric temporal boxes. Both numeric and temporal bounds may be inclusive or not.

    ``TBox`` objects can be created with a single argument of type string as in MobilityDB.

        >>> TBox('TBOXINT XT([0, 10),[2020-06-01, 2020-06-05])')
        >>> TBox('TBOXFLOAT XT([0, 10),[2020-06-01, 2020-06-05])')
        >>> TBox('TBOX T([2020-06-01, 2020-06-05])')

    Another possibility is to provide the ``xmin``/``xmax`` (of type str or
    int/float) and ``tmin``/``tmax`` (of type str or datetime) named parameters, 
    and optionally indicate whether the bounds are inclusive or exclusive (by 
    default, lower bounds are inclusive and upper bounds are exclusive):

        >>> TBox(xmin=0, xmax=10, tmin='2020-06-01', tmax='2020-06-0')
        >>> TBox(xmin=0, xmax=10, tmin='2020-06-01', tmax='2020-06-0', xmax_inc=True, tmax_inc=True)
        >>> TBox(xmin='0', xmax='10', tmin=parse('2020-06-01'), tmax=parse('2020-06-0'))

    Note that you can create a TBox with only the numerical or the temporal dimension. In these cases, it will be
    equivalent to a :class:`~pymeos.time.period.Period` (if it only has temporal dimension) or to a
    :class:`~spans.floatrange` (if it only has the numeric dimension).
    """
    __slots__ = ['_inner']

    def _inner_period(self):
        from pymeos_cffi.functions import _ffi
        return _ffi.addressof(self._inner.period)

    def _inner_span(self):
        from pymeos_cffi.functions import _ffi
        return _ffi.addressof(self._inner.span)

    # ------------------------- Constructors ----------------------------------
    def __init__(self, string: Optional[str] = None, *,
                 xmin: Optional[Union[str, int, float]] = None,
                 xmax: Optional[Union[str, int, float]] = None,
                 tmin: Optional[Union[str, datetime]] = None,
                 tmax: Optional[Union[str, datetime]] = None,
                 xmin_inc: bool = True,
                 xmax_inc: bool = False,
                 tmin_inc: bool = True,
                 tmax_inc: bool = False,
                 _inner=None):
        assert (_inner is not None) or (string is not None) != (
                (xmin is not None and xmax is not None) or (tmin is not None and tmax is not None)), \
            "Either string must be not None or at least a bound pair (xmin/max or tmin/max) must be not None"
        if _inner is not None:
            self._inner = _inner
        elif string is not None:
            self._inner = tbox_in(string)
        else:
            span = None
            period = None
            if xmin is not None and xmax is not None:
                if isinstance(xmin, int) and isinstance(xmax, int):
                    span = intspan_make(xmin, xmax, xmin_inc, xmax_inc)
                else:
                    span = floatspan_make(float(xmin), float(xmax), xmin_inc, xmax_inc)
            if tmin is not None and tmax is not None:
                period = Period(lower=tmin, upper=tmax, lower_inc=tmin_inc, upper_inc=tmax_inc)._inner
            self._inner = tbox_make(span, period)

    def __copy__(self) -> TBox:
        """
        Returns a copy of ``self``.

        Returns:
            A :class:`TBox` instance.

        MEOS Functions:
            tbox_copy
        """
        inner_copy = tbox_copy(self._inner)
        return TBox(_inner=inner_copy)

    @staticmethod
    def from_wkb(wkb: bytes) -> TBox:
        """
        Returns a `TBox` from its WKB representation.

        Args:
            wkb: WKB representation

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            tbox_from_wkb
        """
        result = tbox_from_wkb(wkb)
        return TBox(_inner=result)

    @staticmethod
    def from_hexwkb(hexwkb: str) -> TBox:
        """
        Returns a `TBox` from its WKB representation in hex-encoded ASCII.

        Args:
            hexwkb: WKB representation in hex-encoded ASCII

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            tbox_from_hexwkb
        """
        result = tbox_from_hexwkb(hexwkb)
        return TBox(_inner=result)

    @staticmethod
    def from_value(value: Union[int, float, intrange, floatrange]) -> TBox:
        """
        Returns a `TBox` from a numeric value or range. The created `TBox` will only have a numerical
        dimension.

        Args:
            value: value to be canverted into a TBox

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            int_to_tbox, float_to_tbox, span_to_tbox, span_to_tbox
        """
        if isinstance(value, int):
            result = int_to_tbox(value)
        elif isinstance(value, float):
            result = float_to_tbox(value)
        elif isinstance(value, intrange):
            result = numspan_to_tbox(intrange_to_intspan(value))
        elif isinstance(value, floatrange):
            result = numspan_to_tbox(floatrange_to_floatspan(value))
        else:
            raise TypeError(f'Operation not supported with type {value.__class__}')
        return TBox(_inner=result)

    @staticmethod
    def from_time(time: Time) -> TBox:
        """
        Returns a `TBox` from a :class:`~pymeos.time.time.Time` object. The created `TBox`
        will only have a temporal dimension.

        Args:
            time: value to be canverted into a TBox

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            timestamp_to_tbox, timestampset_to_tbox, period_to_tbox, periodset_to_tbox
        """
        if isinstance(time, datetime):
            result = timestamp_to_tbox(datetime_to_timestamptz(time))
        elif isinstance(time, TimestampSet):
            result = timestampset_to_tbox(time._inner)
        elif isinstance(time, Period):
            result = period_to_tbox(time._inner)
        elif isinstance(time, PeriodSet):
            result = periodset_to_tbox(time._inner)
        else:
            raise TypeError(f'Operation not supported with type {time.__class__}')
        return TBox(_inner=result)

    @staticmethod
    def from_value_time(value: Union[int, float, intrange, floatrange],
                        time: Union[datetime, Period]) -> TBox:
        """
        Returns a `TBox` from a numerical and a temporal object.

        Args:
            value: numerical span of the TBox
            time: temporal span of the TBox

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
        int_timestamp_to_tbox, int_period_to_tbox, float_timestamp_to_tbox, float_period_to_tbox,
        span_timestamp_to_tbox, span_period_to_tbox
        """
        if isinstance(value, int) and isinstance(time, datetime):
            result = int_timestamp_to_tbox(value, datetime_to_timestamptz(time))
        elif isinstance(value, int) and isinstance(time, Period):
            result = int_period_to_tbox(value, time._inner)
        elif isinstance(value, float) and isinstance(time, datetime):
            result = float_timestamp_to_tbox(value, datetime_to_timestamptz(time))
        elif isinstance(value, float) and isinstance(time, Period):
            result = float_period_to_tbox(value, time._inner)
        elif isinstance(value, intrange) and isinstance(time, datetime):
            result = span_timestamp_to_tbox(intrange_to_intspan(value), datetime_to_timestamptz(time))
        elif isinstance(value, intrange) and isinstance(time, Period):
            result = span_period_to_tbox(intrange_to_intspan(value), time._inner)
        elif isinstance(value, floatrange) and isinstance(time, datetime):
            result = span_timestamp_to_tbox(floatrange_to_floatspan(value), datetime_to_timestamptz(time))
        elif isinstance(value, floatrange) and isinstance(time, Period):
            result = span_period_to_tbox(floatrange_to_floatspan(value), time._inner)
        else:
            raise TypeError(f'Operation not supported with types {value.__class__} and {time.__class__}')
        return TBox(_inner=result)

    @staticmethod
    def from_tnumber(temporal: TNumber) -> TBox:
        """
        Returns a `TBox` from a :class:`~pymeos.main.tnumber.TNumber` object.

        Args:
            temporal: temporal number to be canverted into a TBox

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            tnumber_to_tbox
        """
        return TBox(_inner=tnumber_to_tbox(temporal._inner))

    # ------------------------- Output ----------------------------------------
    def __str__(self, max_decimals: int = 15):
        """
        Returns a string representation of ``self``.

        Returns:
            A :class:`str` instance.

        MEOS Functions:
            tbox_out
        """
        return tbox_out(self._inner, max_decimals)

    def __repr__(self):
        """
        Returns a string representation of ``self``.

        Returns:
            A :class:`str` instance.

        MEOS Functions:
            tbox_out
        """
        return (f'{self.__class__.__name__}'
                f'({self})')

    def as_wkb(self) -> str:
        """
        Returns the WKB representation of ``self``.

        Returns:
            A :class:`str` object with the WKB representation of ``self``.

        MEOS Functions:
            tbox_as_wkb
        """
        return tbox_as_wkb(self._inner, 4)

    def as_hexwkb(self) -> str:
        """
        Returns the WKB representation of ``self`` in hex-encoded ASCII.

        Returns:
            A :class:`str` object with the WKB representation of ``self`` in hex-encoded ASCII.

        MEOS Functions:
            tbox_as_hexwkb
        """
        return tbox_as_hexwkb(self._inner, -1)[0]

    # ------------------------- Conversions ----------------------------------
    def to_floatrange(self) -> floatrange:
        """
        Returns the numeric span of ``self``.

        Returns:
            A new :class:`~spans.floatrange` instance

        MEOS Functions:
            tbox_to_floatspan
        """
        return floatspan_to_floatrange(tbox_to_floatspan(self._inner))

    def to_period(self) -> Period:
        """
        Returns the temporal span of ``self``.

        Returns:
            A new :class:`~pymeos.time.period.Period` instance

        MEOS Functions:
            tbox_to_period
        """
        return Period(_inner=tbox_to_period(self._inner))

    # ------------------------- Accessors -------------------------------------
    def has_x(self) -> bool:
        """
        Returns whether ``self`` has a numeric dimension.

        Returns:
            True if ``self`` has a numeric dimension, False otherwise

        MEOS Functions:
            tbox_hasx
        """
        return tbox_hasx(self._inner)

    def has_t(self) -> bool:
        """
        Returns whether ``self`` has a temporal dimension.

        Returns:
            True if ``self`` has a temporal dimension, False otherwise

        MEOS Functions:
            tbox_hast
        """
        return tbox_hast(self._inner)

    def xmin(self) -> float:
        """
        Returns the numeric lower bound of ``self``.

        Returns:
            The numeric lower bound of the `TBox` as a :class:`float`

        MEOS Functions:
            tbox_xmin
        """
        return tbox_xmin(self._inner)

    def xmin_inc(self) -> bool:
        """
        Returns whether the xmin value of the tbox is inclusive or not

        Returns:
            True if the xmin value of the tbox is inclusive and False otherwise

        MEOS Functions:
            tbox_xmin_inc
        """
        return tbox_xmin_inc(self._inner)

    def xmax(self) -> float:
        """
        Returns the numeric upper bound of ``self``.

        Returns:
            The numeric upper bound of the `TBox` as a :class:`float`

        MEOS Functions:
            tbox_xmax
        """
        return tbox_xmax(self._inner)

    def xmax_inc(self) -> bool:
        """
        Returns whether the xmax value of the tbox is inclusive or not

        Returns:
            True if the xmax value of the tbox is inclusive and False otherwise

        MEOS Functions:
            tbox_xmax_inc
        """
        return tbox_xmax_inc(self._inner)

    def tmin(self):
        """
        Returns the temporal lower bound of ``self``.

        Returns:
            The temporal lower bound of the `TBox` as a :class:`~datetime.datetime`

        MEOS Functions:
            tbox_tmin
        """
        result = tbox_tmin(self._inner)
        if not result:
            return None
        return timestamptz_to_datetime(result)

    def tmin_inc(self) -> bool:
        """
        Returns whether the tmin value of the tbox is inclusive or not

        Returns:
            True if the tmin value of the tbox is inclusive and False otherwise

        MEOS Functions:
            tbox_tmin_inc
        """
        return tbox_tmin_inc(self._inner)

    def tmax(self):
        """
        Returns the temporal upper bound of ``self``.

        Returns:
            The temporal upper bound of the `TBox` as a :class:`~datetime.datetime`

        MEOS Functions:
            tbox_tmax
        """
        result = tbox_tmax(self._inner)
        if not result:
            return None
        return timestamptz_to_datetime(result)

    def tmax_inc(self) -> bool:
        """
        Returns whether the tmax value of the tbox is inclusive or not

        Returns:
            True if the tmax value of the tbox is inclusive and False otherwise

        MEOS Functions:
            tbox_tmax_inc
        """
        return tbox_tmax_inc(self._inner)

    # ------------------------- Transformation --------------------------------
    def expand(self, other: Union[int, float, timedelta]) -> TBox:
        """
        Returns the result of expanding ``self`` with the ``other``. Depending on the type of ``other``, the expansion
        will be of the numeric dimension (:class:`float`) or temporal (:class:`~datetime.timedelta`).

        Args:
            other: object used to expand ``self``

        Returns:
            A new :class:`TBox` instance.

        MEOS Functions:
            tbox_expand_value, tbox_expand_time
        """
        if isinstance(other, int) or isinstance(other, float):
            result = tbox_expand_value(self._inner, float(other))
        elif isinstance(other, timedelta):
            result = tbox_expand_time(self._inner, timedelta_to_interval(other))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')
        return TBox(_inner=result)

    def shift(self, delta: timedelta) -> TBox:
        """
        Returns a new `TBox` with the time dimension shifted by `delta`.

        Args:
            delta: :class:`datetime.timedelta` instance to shift

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            period_shift_tscale

        See Also:
            :meth:`Period.shift`
        """
        return self.shift_tscale(shift=delta)

    def tscale(self, duration: timedelta) -> TBox:
        """
        Returns a new `TBox` with the time dimension having duration `duration`.

        Args:
            duration: :class:`datetime.timedelta` instance with new duration

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            period_shift_tscale

        See Also:
            :meth:`Period.tscale`
        """
        return self.shift_tscale(duration=duration)

    def shift_tscale(self, shift: Optional[timedelta] = None,
        duration: Optional[timedelta] = None) -> TBox:
        """
        Returns a new TBox with the temporal span shifted by `shift` and duration `duration`.

        Examples:
            >>> tbox = TBox('TBoxInt XT([0, 10),[2020-06-01, 2020-06-05])')
            >>> tbox.shift_tscale(shift=timedelta(days=2), duration=timedelta(days=4))
            >>> 'TBOXINT XT([0, 10),[2020-06-03 00:00:00+02, 2020-06-07 00:00:00+02])'

        Args:
            shift: :class:`datetime.timedelta` instance to shift the start of the temporal span
            duration: :class:`datetime.timedelta` instance representing the duration of the temporal span

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            period_shift_tscale

        See Also:
            :meth:`Period.shift_tscale`
        """
        assert shift is not None or duration is not None, 'shift and duration deltas must not be both None'
        new_inner = tbox_copy(self._inner)
        new_period = get_address(new_inner.period)
        period_shift_tscale(
            new_period,
            timedelta_to_interval(shift) if shift else None,
            timedelta_to_interval(duration) if duration else None,
        )
        return TBox(_inner=new_inner)

    def round(self, maxdd : int = 0) -> TBox:
        """
        Returns `self` rounded to the given number of decimal digits.

        Args:
            maxdd: Maximum number of decimal digits.

        Returns:
            A new :class:`TBox` instance

        MEOS Functions:
            tbox_round
        """
        new_inner = tbox_copy(self._inner)
        tbox_round(new_inner, maxdd)
        return TBox(_inner=new_inner)

    # ------------------------- Set Operations --------------------------------
    def union(self, other: TBox, strict: Optional[bool] = True) -> TBox:
        """
        Returns the union of `self` with `other`.

        Args:
            other: temporal object to merge with
            strict: Whether to fail if the boxes do not intersect.

        Returns:
            A :class:`TBox` instance.

        MEOS Functions:
            union_tbox_tbox
        """
        return TBox(_inner=union_tbox_tbox(self._inner, other._inner, strict))

    def __add__(self, other):
        """
        Returns the union of `self` with `other`. Fails if the union is not contiguous.

        Args:
            other: temporal object to merge with

        Returns:
            A :class:`TBox` instance.

        MEOS Functions:
            union_tbox_tbox
        """
        return self.union(other, False)

    # TODO: Check returning None for empty intersection is the desired behaviour
    def intersection(self, other: TBox) -> Optional[TBox]:
        """
        Returns the intersection of `self` with `other`.

        Args:
            other: temporal object to merge with

        Returns:
            A :class:`TBox` instance if the instersection is not empty, `None` otherwise.

        MEOS Functions:
            intersection_tbox_tbox
        """
        result = intersection_tbox_tbox(self._inner, other._inner)
        return TBox(_inner=result) if result else None

    def __mul__(self, other):
        """
        Returns the intersection of `self` with `other`.

        Args:
            other: temporal object to merge with

        Returns:
            A :class:`TBox` instance if the instersection is not empty, `None` otherwise.

        MEOS Functions:
            intersection_tbox_tbox
        """
        return self.intersection(other)

    # ------------------------- Topological Operations ------------------------
    def is_adjacent(self, other: Union[int, float, intrange, floatrange, TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is adjacent to ``other``. That is, they share only the temporal or numerical bound
        and only one of them contains it.

        Examples:
            >>> TBox('TBoxInt XT([0, 1], [2012-01-01, 2012-01-02))').is_adjacent(TBox('TBoxInt XT([0, 1], [2012-01-02, 2012-01-03])'))
            >>> True
            >>> TBox('TBoxInt XT([0, 1], [2012-01-01, 2012-01-02])').is_adjacent(TBox('TBoxInt XT([0, 1], [2012-01-02, 2012-01-03])'))
            >>> False  # Both contain bound
            >>> TBox('TBoxInt XT([0, 1), [2012-01-01, 2012-01-02))').is_adjacent(TBox('TBoxInt XT([1, 2], [2012-01-02, 2012-01-03])')
            >>> False  # Adjacent in both bounds

        Args:
            other: object to compare with

        Returns:
            True if adjacent, False otherwise

        MEOS Functions:
            adjacent_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, int):
            return adjacent_span_span(self._inner_span(), float_to_floaspan(float(other)))
        elif isinstance(other, float):
            return adjacent_span_span(self._inner_span(), float_to_floaspan(other))
        elif isinstance(other, intrange):
            from pymeos_cffi.functions import _ffi
            return adjacent_span_span(_ffi.addressof(self._inner, 'span'), intrange_to_intspan(other))
        elif isinstance(other, floatrange):
            return adjacent_span_span(self._inner.span, floatrange_to_floatspan(other))
        elif isinstance(other, TBox):
            return adjacent_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return adjacent_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_contained_in(self, container: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is contained in ``container``.

        Examples:
            >>> TBox('TBoxInt XT([1, 2], [2012-01-02, 2012-01-03])').is_contained_in(TBox('TBoxInt XT([1, 4], [2012-01-01, 2012-01-04])'))
            >>> True
            >>> TBox('TBoxFloat XT((1, 2), (2012-01-01, 2012-01-02))').is_contained_in(TBox('TBoxFloat XT([1, 4], [2012-01-01, 2012-01-02])'))
            >>> True
            >>> TBox('TBoxFloat XT([1, 2], [2012-01-01, 2012-01-02])').is_contained_in(TBox('TBoxFloat XT((1, 2), (2012-01-01, 2012-01-02))'))
            >>> False

        Args:
            container: temporal object to compare with

        Returns:
            True if contained, False otherwise

        MEOS Functions:
            contained_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(container, TBox):
            return contained_tbox_tbox(self._inner, container._inner)
        elif isinstance(container, TNumber):
            return contained_tbox_tbox(self._inner, tnumber_to_tbox(container._inner))
        else:
            raise TypeError(f'Operation not supported with type {container.__class__}')

    def contains(self, content: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` temporally contains ``content``.

        Examples:
            >>> TBox('TBoxInt XT([1, 4], [2012-01-01, 2012-01-04]').contains(TBox('TBoxInt XT([2, 3], [2012-01-02, 2012-01-03]'))
            >>> True
            >>> TBox('TBoxFloat XT([1, 2], [2012-01-01, 2012-01-02]').contains(TBox('TBoxFloat XT((1, 2), (2012-01-01, 2012-01-02)'))
            >>> True
            >>> TBox('TBoxFloat XT((1, 2), (2012-01-01, 2012-01-02)').contains(TBox('TBoxFloat XT([1, 2], [2012-01-01, 2012-01-02]'))
            >>> False

        Args:
            content: temporal object to compare with

        Returns:
            True if contains, False otherwise

        MEOS Functions:
            contains_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(content, TBox):
            return contains_tbox_tbox(self._inner, content._inner)
        elif isinstance(content, TNumber):
            return contains_tbox_tbox(self._inner, tnumber_to_tbox(content._inner))
        else:
            raise TypeError(f'Operation not supported with type {content.__class__}')

    def __contains__(self, item):
        """
        Returns whether ``self`` temporally contains ``item``.

        Examples:
            >>> TBox('TBoxInt XT([2, 3], [2012-01-02, 2012-01-03]') in TBox('TBoxInt XT([1, 4], [2012-01-01, 2012-01-04]')
            >>> True
            >>> TBox('TBoxFloat XT((1, 2), (2012-01-01, 2012-01-02)') in TBox('TBoxFloat XT([1, 2], [2012-01-01, 2012-01-02]')
            >>> True
            >>> TBox('TBoxFloat XT([1, 2], [2012-01-01, 2012-01-02]') in TBox('TBoxFloat XT((1, 2), (2012-01-01, 2012-01-02)')
            >>> False

        Args:
            item: temporal object to compare with

        Returns:
            True if contains, False otherwise

        MEOS Functions:
            contains_tbox_tbox, tnumber_to_tbox
        """
        return self.contains(item)

    def overlaps(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` overlaps ``other``. That is, both share at least an instant or a value.

        Args:
            other: temporal object to compare with

        Returns:
            True if overlaps, False otherwise

        MEOS Functions:
            overlaps_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return overlaps_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return overlaps_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_same(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is the same as ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if same, False otherwise

        MEOS Functions:
            same_tbox_tbox, tnumber_to_tbox

        """
        if isinstance(other, TBox):
            return same_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return same_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    # ------------------------- Position Operations ---------------------------
    def is_left(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is strictly to the left of ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if left, False otherwise

        MEOS Functions:
            left_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return left_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return left_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_over_or_left(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is to the left of ``other`` allowing overlap. That is, ``self`` does not extend to the
        right of ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if overleft, False otherwise

        MEOS Functions:
            overleft_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return overleft_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return overleft_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_right(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is strictly to the right of ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if right, False otherwise

        MEOS Functions:
            right_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return right_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return right_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_over_or_right(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is to the right of ``other`` allowing overlap. That is, ``self`` does not extend to the
        left of ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if overright, False otherwise

        MEOS Functions:
            overright_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return overright_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return overright_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_before(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is strictly before ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if before, False otherwise

        MEOS Functions:
            before_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return before_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return before_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_over_or_before(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is before ``other`` allowing overlap. That is, ``self`` does not extend after
        ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if overbefore, False otherwise

        MEOS Functions:
            overbefore_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return overbefore_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return overbefore_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_after(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is strictly after ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if after, False otherwise

        MEOS Functions:
            after_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return after_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return after_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def is_over_or_after(self, other: Union[TBox, TNumber]) -> bool:
        """
        Returns whether ``self`` is after ``other`` allowing overlap. That is, ``self`` does not extend before
        ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if overafter, False otherwise

        MEOS Functions:
            overafter_tbox_tbox, tnumber_to_tbox
        """
        if isinstance(other, TBox):
            return overafter_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return overafter_tbox_tbox(self._inner, tnumber_to_tbox(other._inner))
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    # ------------------------- Distance Operations ---------------------------
    def nearest_approach_distance(self, other: Union[TBox, TNumber]) -> float:
        """
        Returns the distance between the nearest points of ``self`` and ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            A :class:`float` with the distance between the nearest points of ``self`` and ``other``.

        MEOS Functions:
            nad_tbox_tbox
        """
        if isinstance(other, TBox):
            return nad_tbox_tbox(self._inner, other._inner)
        elif isinstance(other, TNumber):
            return nad_tnumber_tbox(other._inner, self._inner)
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    # ------------------------- Splitting --------------------------------------
    def tile(self, size: float, duration: Union[timedelta, str],
             origin: float = 0.0, start: Union[datetime, str, None] = None) -> List[List[TBox]]:
        """
        Returns 2d matrix of TBoxes resulting of tiling ``self``.

        Args:
            size: size of the numeric dimension of the tiles
            duration: size of the temporal dimenstion of the tiles
            origin: origin of the numeric dimension of the tiles
            start: origin of the temporal dimension of the tiles

        Returns:
            A 2d array of :class:`TBox` instances.

        MEOS Functions:
            tbox_tile_list
        """
        dt = timedelta_to_interval(duration) if isinstance(duration, timedelta) else pg_interval_in(duration, -1)
        st = datetime_to_timestamptz(start) if isinstance(start, datetime) \
            else pg_timestamptz_in(start, -1) if isinstance(start, str) \
            else tbox_tmin(self._inner)
        tiles, rows, columns = tbox_tile_list(self._inner, size, dt, origin, st)
        return [[TBox(_inner=tiles + (c * rows + r)) for c in range(columns)] for r in range(rows)]

    def tile_flat(self, size: float, duration: Union[timedelta, str],
                  origin: float = 0.0, start: Union[datetime, str, None] = None) -> List[TBox]:
        """
        Returns an array of TBoxes resulting of tiling ``self``.

        Args:
            size: size of the numeric dimension of the tiles
            duration: size of the temporal dimenstion of the tiles
            origin: origin of the numeric dimension of the tiles
            start: origin of the temporal dimension of the tiles

        Returns:
            An array of :class:`TBox` instances.

        MEOS Functions:
            tbox_tile_list
        """
        tiles = self.tile(size, duration, origin, start)
        return [box for row in tiles for box in row]

    # ------------------------- Comparisons -----------------------------------
    def __eq__(self, other):
        """
        Returns whether ``self`` is equal to ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if equal, False otherwise

        MEOS Functions:
            tbox_eq
        """
        if isinstance(other, self.__class__):
            return tbox_eq(self._inner, other._inner)
        return False

    def __ne__(self, other):
        """
        Returns whether ``self`` is not equal to ``other``.

        Args:
            other: temporal object to compare with

        Returns:
            True if not equal, False otherwise

        MEOS Functions:
            tbox_ne
        """
        if isinstance(other, self.__class__):
            return tbox_ne(self._inner, other._inner)
        return True

    def __lt__(self, other):
        """
        Returns whether ``self`` is less than ``other``. The time dimension is compared first, then the space dimension.

        Args:
            other: temporal object to compare with

        Returns:
            True if less than, False otherwise

        MEOS Functions:
            tbox_lt
        """
        if isinstance(other, self.__class__):
            return tbox_lt(self._inner, other._inner)
        raise TypeError(f'Operation not supported with type {other.__class__}')

    def __le__(self, other):
        """
        Returns whether ``self`` is less than or equal to ``other``. The time dimension is compared first, then the
        space dimension.

        Args:
            other: temporal object to compare with

        Returns:
            True if less than or equal to, False otherwise

        MEOS Functions:
            tbox_le
        """
        if isinstance(other, self.__class__):
            return tbox_le(self._inner, other._inner)
        raise TypeError(f'Operation not supported with type {other.__class__}')

    def __gt__(self, other):
        """
        Returns whether ``self`` is greater than ``other``. The time dimension is compared first, then the space
        dimension.

        Args:
            other: temporal object to compare with

        Returns:
            True if greater than, False otherwise

        MEOS Functions:
            tbox_gt
        """
        if isinstance(other, self.__class__):
            return tbox_gt(self._inner, other._inner)
        raise TypeError(f'Operation not supported with type {other.__class__}')

    def __ge__(self, other):
        """
        Returns whether ``self`` is greater than or equal to ``other``. The time dimension is compared first, then the
        space dimension.

        Args:
            other: temporal object to compare with

        Returns:
            True if greater than or equal to, False otherwise

        MEOS Functions:
            tbox_ge
        """
        if isinstance(other, self.__class__):
            return tbox_ge(self._inner, other._inner)
        raise TypeError(f'Operation not supported with type {other.__class__}')

    # ------------------------- Plot Operations -------------------------------
    def plot(self, *args, **kwargs):
        """
        Plots ``self``.

        See Also:
            :func:`~pymeos.plotters.box_plotter.BoxPlotter.plot_tbox`
        """
        from ..plotters import BoxPlotter
        return BoxPlotter.plot_tbox(self, *args, **kwargs)

    # ------------------------- Database Operations ---------------------------
    @staticmethod
    def read_from_cursor(value, _=None):
        """
        Reads a :class:`TBox` from a database cursor. Used when automatically loading objects from the database.
        Users should use the class constructor instead.
        """
        if not value:
            return None
        return TBox(string=value)
