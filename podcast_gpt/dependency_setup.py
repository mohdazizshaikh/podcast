"""Explicit optional application-venv package installation, never model weights."""
import importlib.metadata
import os
import subprocess
import sys

ACK="I_AUTHORIZE_INSTALLING_FREE_OPTIONAL_PYTHON_PACKAGES"
GROUPS={"documents":("pypdf>=5,<8",),"kokoro":("kokoro-onnx>=0.4,<1","misaki>=0.9,<1"),
        "kokoro-english":("kokoro-onnx>=0.4,<1","misaki[en]>=0.9,<1")}


def plan(group):
    if group not in GROUPS:raise ValueError("Select a supported optional dependency group")
    packages=[]
    for spec in GROUPS[group]:
        name=spec.split(">=")[0].split("[")[0]
        try:version=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:version=None
        packages.append({"requirement":spec,"installed_version":version})
    return {"group":group,"packages":packages,"app_virtual_environment":sys.prefix!=sys.base_prefix,
            "requires_explicit_install_consent":True,"model_downloads":0,"model_load_verified":False}


def install(group,*,acknowledgment,runner=None):
    result=plan(group)
    if acknowledgment!=ACK:raise ValueError("Explicit optional package installation acknowledgment required")
    if sys.prefix==sys.base_prefix:raise ValueError("Use the app virtual environment; never install globally")
    run=runner or subprocess.run
    # Ignore user pip index settings; no arbitrary package names, extra indexes,
    # shell interpolation, upgrades, or model download commands.
    env={k:v for k,v in os.environ.items() if not k.upper().startswith("PIP_")}
    env["PIP_CONFIG_FILE"]=os.devnull
    args=[sys.executable,"-m","pip","--disable-pip-version-check","--no-input","install",
          "--index-url","https://pypi.org/simple",*GROUPS[group]]
    for cmd in (args,[sys.executable,"-m","pip","--disable-pip-version-check","check"]):
        try:completed=run(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=900,check=False)
        except subprocess.TimeoutExpired:raise ValueError("Optional package installation/check timed out; inspect environment manually") from None
        if completed.returncode:raise ValueError("Optional package installation/check failed; inspect app environment locally")
    return {**plan(group),"pip_check_passed":True,"installation_command_completed":True,
            "model_load_verified":False,"third_party_weights_installed":False}
