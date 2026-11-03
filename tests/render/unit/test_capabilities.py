from scene_signal.render.domain.capabilities import RendererCapabilities

def test_renderer_capabilities_defaults():
    caps = RendererCapabilities()
    assert caps.contract_versions == ["1.0"]
    assert caps.schemes == ["file"]
    assert caps.containers == ["mp4"]
    assert caps.video_codecs == ["h264"]
    assert caps.audio_codecs == ["aac"]
    assert caps.audio_modes == ["mute", "source"]
    assert caps.features.render_engine is True
