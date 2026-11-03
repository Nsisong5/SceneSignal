from scene_signal.render.domain.geometry import compute_fit

def test_compute_fit_letterbox():
    res = compute_fit(
        src_width=1080,
        src_height=1920,
        target_width=1280,
        target_height=720,
        fit_mode="letterbox",
    )
    assert res.scaled_width % 2 == 0
    assert res.scaled_height % 2 == 0
    assert res.pad_width == 1280
    assert res.pad_height == 720

def test_compute_fit_crop():
    res = compute_fit(
        src_width=1080,
        src_height=1920,
        target_width=1280,
        target_height=720,
        fit_mode="crop",
    )
    assert res.scaled_width % 2 == 0
    assert res.scaled_height % 2 == 0
    assert res.crop_width == 1280
    assert res.crop_height == 720
