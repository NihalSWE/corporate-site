import json
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage


CONTACT_ADDRESS_SEPARATOR = "\n---address---\n"
TEAM_PROFILE_STORE = Path(settings.BASE_DIR) / "backend" / "team_profile_descriptions.json"
SISTER_CONCERN_GALLERY_STORE = Path(settings.BASE_DIR) / "backend" / "sister_concern_gallery.json"
SISTER_CONCERN_GALLERY_LIMIT = 10


def split_contact_addresses(address):
    if not address:
        return []
    if CONTACT_ADDRESS_SEPARATOR in address:
        return [item.strip() for item in address.split(CONTACT_ADDRESS_SEPARATOR) if item.strip()]
    return [address.strip()] if address.strip() else []


def pack_contact_addresses(addresses):
    cleaned = [item.strip() for item in addresses if item and item.strip()]
    return CONTACT_ADDRESS_SEPARATOR.join(cleaned)


def get_contact_address_fields(address, total=3):
    fields = split_contact_addresses(address)
    while len(fields) < total:
        fields.append("")
    return fields[:total]


def load_team_profile_descriptions():
    if not TEAM_PROFILE_STORE.exists():
        return {}
    try:
        with TEAM_PROFILE_STORE.open("r", encoding="utf-8") as profile_file:
            data = json.load(profile_file)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_team_profile_descriptions(data):
    TEAM_PROFILE_STORE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_team_profile_description(member_id):
    return load_team_profile_descriptions().get(str(member_id), "")


def set_team_profile_description(member_id, description):
    data = load_team_profile_descriptions()
    key = str(member_id)
    if description and description.strip():
        data[key] = description.strip()
    else:
        data.pop(key, None)
    save_team_profile_descriptions(data)


def delete_team_profile_description(member_id):
    data = load_team_profile_descriptions()
    data.pop(str(member_id), None)
    save_team_profile_descriptions(data)


def load_sister_concern_gallery():
    if not SISTER_CONCERN_GALLERY_STORE.exists():
        return {}
    try:
        with SISTER_CONCERN_GALLERY_STORE.open("r", encoding="utf-8") as gallery_file:
            data = json.load(gallery_file)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_sister_concern_gallery(data):
    SISTER_CONCERN_GALLERY_STORE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def storage_path_exists(path):
    try:
        return bool(path and default_storage.exists(path))
    except (OSError, ValueError):
        return False


def get_sister_concern_gallery_paths(concern_id):
    data = load_sister_concern_gallery()
    key = str(concern_id)
    paths = data.get(key, [])
    if not isinstance(paths, list):
        return []
    existing_paths = [path for path in paths if storage_path_exists(path)]
    if existing_paths != paths:
        data[key] = existing_paths
        save_sister_concern_gallery(data)
    return existing_paths


def get_sister_concern_gallery_urls(concern_id):
    return [default_storage.url(path) for path in get_sister_concern_gallery_paths(concern_id)]


def get_sister_concern_gallery_items(concern_id):
    return [
        {
            "path": path,
            "url": default_storage.url(path),
        }
        for path in get_sister_concern_gallery_paths(concern_id)
    ]


def add_sister_concern_gallery_images(concern_id, images):
    if not images:
        return 0

    data = load_sister_concern_gallery()
    key = str(concern_id)
    existing = data.get(key, [])
    if not isinstance(existing, list):
        existing = []
    existing = [path for path in existing if storage_path_exists(path)]

    remaining = SISTER_CONCERN_GALLERY_LIMIT - len(existing)
    if remaining <= 0:
        return 0

    saved_paths = []
    for image in images[:remaining]:
        path = f"sister_concerns/gallery/{concern_id}/{image.name}"
        saved_paths.append(default_storage.save(path, image))

    data[key] = existing + saved_paths
    save_sister_concern_gallery(data)
    return len(saved_paths)


def remove_sister_concern_gallery_image(concern_id, image_path):
    data = load_sister_concern_gallery()
    key = str(concern_id)
    existing = data.get(key, [])
    if image_path in existing:
        existing.remove(image_path)
        default_storage.delete(image_path)
        data[key] = existing
        save_sister_concern_gallery(data)


def delete_sister_concern_gallery(concern_id):
    data = load_sister_concern_gallery()
    paths = data.pop(str(concern_id), [])
    for path in paths:
        default_storage.delete(path)
    save_sister_concern_gallery(data)


def existing_file_url(file_field):
    if not file_field:
        return ""
    try:
        if default_storage.exists(file_field.name):
            return file_field.url
    except (OSError, ValueError):
        return ""
    return ""


def attach_sister_concern_asset_urls(concern):
    concern.logo_existing_url = existing_file_url(concern.logo)
    concern.display_image_existing_url = existing_file_url(concern.display_image)
    return concern
