from podcast_gpt import voice_preflight,device_acceptance,projects,web,cli,dashboard_authoring as author
from test_v4_master_tts import ready
from test_v4_dashboard_actions import request


def test_duplicate_and_missing_paths(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch,"kokoro",presets=("hm_omega","hm_omega"))
    result=voice_preflight.inspect(root,pid)
    assert not result["static_preflight_clear"] and not result["runtime_voice_compatibility_verified"]
    assert all("duplicate_preset" in row["issues"] for row in result["voices"])
    assert all("saved_paths_not_checked" in row["issues"] for row in result["voices"])
    assert author.run(root,"voice-preflight",{"project_id":pid})==result


def test_language_mismatch(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch,"kokoro",language="Spanish",presets=("hm_omega","hf_alpha"))
    assert all("kokoro_language_or_preset_mismatch" in row["issues"] for row in voice_preflight.inspect(root,pid)["voices"])


def test_initial_acceptance_and_markup(tmp_path):
    root=tmp_path/"private";pid=projects.create(root,request())["project_id"]
    result=device_acceptance.inspect(root,pid)
    assert result["readiness"]["stage"]=="outline_required"
    assert not result["physical_device_acceptance_verified"] and not result["production_release_approved"]
    assert result["measured_audio_seconds"] is None and not result["voice_preflight"]["cast_assigned"]
    assert "v4VoicePreflight" in web.html_page("test") and "v4TurnDiagnostics" in web.html_page("test")
    assert cli.parse(["project-device-acceptance","--project-id",pid]).operation=="project-device-acceptance"
