import json
import os
from pathlib import Path


PROFILE_ENV_VAR = "LILITH_DIALOGUE_PROFILE"
PROFILE_VERSION = 1

DEFAULT_PROFILE = {
    "profile_version": PROFILE_VERSION,
    "user_name": "Alex",
    "character_name": "Lilith",
    "language": "ru",
    "grammatical_gender": "feminine",
    "max_beats": 4,
    "roleplay_intensity": 2,
    "personality_mode": "auto",
}

ALLOWED_LANGUAGES = {"ru", "en"}
ALLOWED_GENDERS = {"feminine", "masculine", "neutral"}
ALLOWED_PERSONALITY_MODES = {"auto", "tender", "playful", "jealous", "comforting"}
ALLOWED_KEYS = set(DEFAULT_PROFILE)


class ProfileError(ValueError):
    pass


def default_profile_path(env=None, home=None):
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)

    override = env.get(PROFILE_ENV_VAR)
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        config_root = Path(env.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        config_root = Path(env.get("XDG_CONFIG_HOME", home / ".config"))
    return config_root / "lilith-dialogue" / "profile.json"


def validate_profile(raw):
    if not isinstance(raw, dict):
        raise ProfileError("the profile root must be a JSON object")

    unknown = sorted(set(raw) - ALLOWED_KEYS)
    if unknown:
        raise ProfileError(f"unknown profile fields: {', '.join(unknown)}")

    profile = DEFAULT_PROFILE | raw

    version = profile["profile_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != PROFILE_VERSION:
        raise ProfileError(
            f"unsupported profile_version {version!r}; "
            f"expected {PROFILE_VERSION}"
        )

    for field in ("user_name", "character_name"):
        value = profile[field]
        if not isinstance(value, str) or not value.strip():
            raise ProfileError(f"{field} must be a non-empty string")
        profile[field] = " ".join(value.split())[:80]

    if profile["language"] not in ALLOWED_LANGUAGES:
        allowed = ", ".join(sorted(ALLOWED_LANGUAGES))
        raise ProfileError(f"language must be one of: {allowed}")

    if profile["grammatical_gender"] not in ALLOWED_GENDERS:
        allowed = ", ".join(sorted(ALLOWED_GENDERS))
        raise ProfileError(f"grammatical_gender must be one of: {allowed}")

    max_beats = profile["max_beats"]
    if isinstance(max_beats, bool) or not isinstance(max_beats, int) or not 1 <= max_beats <= 4:
        raise ProfileError("max_beats must be an integer from 1 to 4")

    intensity = profile["roleplay_intensity"]
    if isinstance(intensity, bool) or not isinstance(intensity, int) or not 0 <= intensity <= 3:
        raise ProfileError("roleplay_intensity must be an integer from 0 to 3")

    if profile["personality_mode"] not in ALLOWED_PERSONALITY_MODES:
        allowed = ", ".join(sorted(ALLOWED_PERSONALITY_MODES))
        raise ProfileError(f"personality_mode must be one of: {allowed}")

    return profile


def load_profile(path=None):
    path = default_profile_path() if path is None else Path(path).expanduser()
    if not path.exists():
        return DEFAULT_PROFILE.copy(), path, None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return validate_profile(raw), path, None
    except (OSError, UnicodeError, json.JSONDecodeError, ProfileError) as exc:
        warning = f"Could not load dialogue profile from {path}: {exc}. Using defaults."
        return DEFAULT_PROFILE.copy(), path, warning
