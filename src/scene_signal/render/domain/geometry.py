from fractions import Fraction
from typing import Literal, NamedTuple

class GeometryResult(NamedTuple):
    scaled_width: int
    scaled_height: int
    crop_x: int
    crop_y: int
    crop_width: int
    crop_height: int
    pad_width: int
    pad_height: int
    pad_x: int
    pad_y: int

def floor_even(val: int | float | Fraction) -> int:
    i = int(val)
    if i % 2 != 0:
        i -= 1
    return max(2, i)

def ceil_even(val: int | float | Fraction) -> int:
    i = int(val)
    if i % 2 != 0:
        i += 1
    return max(2, i)

def compute_fit(
    src_width: int,
    src_height: int,
    sar_num: int = 1,
    sar_den: int = 1,
    rotation: int = 0,
    target_width: int = 1280,
    target_height: int = 720,
    fit_mode: Literal["letterbox", "crop"] = "letterbox",
) -> GeometryResult:
    # Handle rotation
    if rotation in (90, 270):
        w = src_height
        h = src_width
    else:
        w = src_width
        h = src_height

    # SAR adjustment
    sar = Fraction(sar_num, sar_den)
    effective_w = Fraction(w) * sar

    target_w = Fraction(target_width)
    target_h = Fraction(target_height)

    if fit_mode == "letterbox":
        # Scale to fit inside target while maintaining aspect ratio
        scale_w = target_w / effective_w
        scale_h = target_h / Fraction(h)
        scale = min(scale_w, scale_h)

        scaled_w = floor_even(effective_w * scale)
        scaled_h = floor_even(Fraction(h) * scale)

        pad_w = floor_even((target_w - scaled_w) / 2)
        pad_h = floor_even((target_h - scaled_h) / 2)

        return GeometryResult(
            scaled_width=scaled_w,
            scaled_height=scaled_h,
            crop_x=0,
            crop_y=0,
            crop_width=scaled_w,
            crop_height=scaled_h,
            pad_width=target_width,
            pad_height=target_height,
            pad_x=int(pad_w),
            pad_y=int(pad_h),
        )
    else:  # crop
        scale_w = target_w / effective_w
        scale_h = target_h / Fraction(h)
        scale = max(scale_w, scale_h)

        scaled_w = ceil_even(effective_w * scale)
        scaled_h = ceil_even(Fraction(h) * scale)

        crop_x = floor_even((scaled_w - target_w) / 2)
        crop_y = floor_even((scaled_h - target_h) / 2)

        return GeometryResult(
            scaled_width=scaled_w,
            scaled_height=scaled_h,
            crop_x=int(crop_x),
            crop_y=int(crop_y),
            crop_width=target_width,
            crop_height=target_height,
            pad_width=target_width,
            pad_height=target_height,
            pad_x=0,
            pad_y=0,
        )
