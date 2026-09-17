from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = os.getenv("SKIN_API_BASE_URL", "https://yce-api-01.makeupar.com")
API_VERSION = os.getenv("SKIN_API_VERSION", "v2.1")

HD_ACTIONS = [
    "hd_wrinkle", "hd_pore", "hd_texture", "hd_acne", "hd_oiliness",
    "hd_radiance", "hd_eye_bag", "hd_age_spot", "hd_dark_circle",
    "hd_droopy_upper_eyelid", "hd_droopy_lower_eyelid", "hd_firmness",
    "hd_moisture", "hd_redness", "hd_tear_trough", "hd_skin_type",
]

SD_ACTIONS = [
    "wrinkle", "pore", "texture", "acne", "oiliness", "radiance",
    "eye_bag", "age_spot", "dark_circle_v2", "droopy_upper_eyelid",
    "droopy_lower_eyelid", "firmness", "moisture", "redness",
    "tear_trough", "skin_type",
]


class SkinAPIError(RuntimeError):
    pass


@dataclass
class UploadedFile:
    file_id: str
    file_name: str
    content_type: str


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _json_or_error(resp: requests.Response, context: str) -> dict[str, Any]:
    try:
        payload = resp.json()
    except Exception:
        payload = {}

    if not resp.ok:
        message = payload.get("error") or payload.get("message") or resp.text[:500]
        code = payload.get("error_code")
        if code:
            message = f"{message} ({code})"
        raise SkinAPIError(f"{context}: HTTP {resp.status_code}: {message}")

    status = payload.get("status")
    if isinstance(status, int) and status >= 400:
        message = payload.get("error") or payload.get("message") or str(payload)
        raise SkinAPIError(f"{context}: API status {status}: {message}")

    return payload


def _normalize_content_type(content_type: str) -> str:
    content_type = (content_type or "image/jpeg").lower()
    if content_type in {"image/jpeg", "image/jpg"}:
        return "image/jpg"
    if content_type == "image/png":
        return "image/png"
    return content_type


def upload_image(
    api_key: str,
    image_bytes: bytes,
    *,
    filename: str,
    content_type: str,
    timeout: int = 45,
) -> UploadedFile:
    content_type = _normalize_content_type(content_type)
    if content_type == "image/jpg" and not filename.lower().endswith((".jpg", ".jpeg")):
        filename = "skin_scan.jpg"

    metadata = {
        "files": [{
            "content_type": content_type,
            "file_name": filename,
            "file_size": len(image_bytes),
        }]
    }

    response = requests.post(
        f"{BASE_URL}/s2s/v2.0/file",
        headers=_headers(api_key),
        json=metadata,
        timeout=timeout,
    )
    payload = _json_or_error(response, "Create upload")

    try:
        info = payload["data"]["files"][0]
        request_info = info["requests"][0]
    except Exception as exc:
        raise SkinAPIError(f"Create upload: unexpected response shape: {payload}") from exc

    upload_response = requests.request(
        str(request_info.get("method", "PUT")).upper(),
        request_info["url"],
        headers={str(k): str(v) for k, v in (request_info.get("headers") or {}).items()},
        data=image_bytes,
        timeout=timeout,
    )
    if not upload_response.ok:
        raise SkinAPIError(
            f"Upload image: HTTP {upload_response.status_code}: "
            f"{upload_response.text[:400]}"
        )

    return UploadedFile(
        file_id=str(info["file_id"]),
        file_name=str(info.get("file_name", filename)),
        content_type=str(info.get("content_type", content_type)),
    )


def start_skin_analysis(
    api_key: str,
    file_id: str,
    *,
    hd: bool,
    timeout: int = 45,
) -> str:
    body = {
        "src_file_id": file_id,
        "dst_actions": HD_ACTIONS if hd else SD_ACTIONS,
        "format": "json",
        "pf_camera_kit": False,
    }

    response = requests.post(
        f"{BASE_URL}/s2s/{API_VERSION}/task/skin-analysis",
        headers=_headers(api_key),
        json=body,
        timeout=timeout,
    )
    payload = _json_or_error(response, "Start skin analysis")

    try:
        return str(payload["data"]["task_id"])
    except Exception as exc:
        raise SkinAPIError(f"Start skin analysis: task_id missing: {payload}") from exc


def poll_skin_analysis(
    api_key: str,
    task_id: str,
    *,
    timeout_seconds: int = 240,
    poll_interval_seconds: float = 6.0,
    on_poll=None,
) -> dict[str, Any]:
    url = f"{BASE_URL}/s2s/{API_VERSION}/task/skin-analysis/{task_id}"
    deadline = time.time() + timeout_seconds
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        response = requests.get(url, headers=_headers(api_key), timeout=45)
        payload = _json_or_error(response, "Poll skin analysis")
        data = payload.get("data") or {}
        status = str(data.get("task_status") or "").lower()

        if on_poll:
            on_poll(attempt, status or "running")

        if status == "success":
            return payload
        if status == "error":
            raise SkinAPIError(f"Skin analysis failed: {data.get('error') or data}")

        time.sleep(poll_interval_seconds)

    raise SkinAPIError(f"Skin analysis did not finish within {timeout_seconds} seconds.")


def run_skin_analysis(
    api_key: str,
    image_bytes: bytes,
    *,
    hd: bool,
    filename: str,
    content_type: str,
    on_poll=None,
) -> dict[str, Any]:
    uploaded = upload_image(
        api_key,
        image_bytes,
        filename=filename,
        content_type=content_type,
    )
    task_id = start_skin_analysis(api_key, uploaded.file_id, hd=hd)
    return poll_skin_analysis(api_key, task_id, on_poll=on_poll)


def output_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") or {}
    results = data.get("results") or {}
    output = results.get("output") or []
    return [item for item in output if isinstance(item, dict)]
