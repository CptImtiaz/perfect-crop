from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
import requests

BASE_URL = "https://yce-api-01.makeupar.com"

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


class PerfectCorpError(RuntimeError):
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
        msg = payload.get("error") or payload.get("message") or resp.text[:500]
        code = payload.get("error_code")
        if code:
            msg = f"{msg} ({code})"
        raise PerfectCorpError(f"{context}: HTTP {resp.status_code}: {msg}")

    status = payload.get("status")
    if isinstance(status, int) and status >= 400:
        msg = payload.get("error") or payload.get("message") or str(payload)
        raise PerfectCorpError(f"{context}: API status {status}: {msg}")

    return payload


def upload_image(
    api_key: str,
    image_bytes: bytes,
    *,
    filename: str,
    content_type: str,
    timeout: int = 30,
) -> UploadedFile:
    meta = {
        "files": [{
            "content_type": content_type,
            "file_name": filename,
            "file_size": len(image_bytes),
        }]
    }

    resp = requests.post(
        f"{BASE_URL}/s2s/v2.0/file",
        headers=_headers(api_key),
        json=meta,
        timeout=timeout,
    )
    payload = _json_or_error(resp, "Create upload")

    try:
        info = payload["data"]["files"][0]
        request_info = info["requests"][0]
    except Exception as exc:
        raise PerfectCorpError(
            f"Create upload: unexpected response shape: {payload}"
        ) from exc

    upload_resp = requests.request(
        str(request_info.get("method", "PUT")).upper(),
        request_info["url"],
        headers={str(k): str(v) for k, v in (request_info.get("headers") or {}).items()},
        data=image_bytes,
        timeout=timeout,
    )
    if not upload_resp.ok:
        raise PerfectCorpError(
            f"Upload image: HTTP {upload_resp.status_code}: "
            f"{upload_resp.text[:400]}"
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
    timeout: int = 30,
) -> str:
    body = {
        "src_file_id": file_id,
        "dst_actions": HD_ACTIONS if hd else SD_ACTIONS,
        "miniserver_args": {
            "enable_mask_overlay": True,
            "enable_dark_background_hd_pore": True,
            "color_dark_background_hd_pore": "3D3D3D",
            "opacity_dark_background_hd_pore": 0.4,
            "enable_dark_background_hd_wrinkle": True,
            "color_dark_background_hd_wrinkle": "3D3D3D",
            "opacity_dark_background_hd_wrinkle": 0.4,
        },
        "format": "json",
        "pf_camera_kit": True,
    }

    resp = requests.post(
        f"{BASE_URL}/s2s/v2.1/task/skin-analysis",
        headers=_headers(api_key),
        json=body,
        timeout=timeout,
    )
    payload = _json_or_error(resp, "Start skin analysis")

    try:
        return str(payload["data"]["task_id"])
    except Exception as exc:
        raise PerfectCorpError(f"task_id missing: {payload}") from exc


def poll_skin_analysis(
    api_key: str,
    task_id: str,
    *,
    timeout_seconds: int = 180,
    poll_interval_seconds: float = 5.0,
    on_poll=None,
) -> dict[str, Any]:
    url = f"{BASE_URL}/s2s/v2.1/task/skin-analysis/{task_id}"
    deadline = time.time() + timeout_seconds
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        resp = requests.get(url, headers=_headers(api_key), timeout=30)
        payload = _json_or_error(resp, "Poll skin analysis")
        data = payload.get("data") or {}
        status = str(data.get("task_status") or "").lower()

        if on_poll:
            on_poll(attempt, status or "running")

        if status == "success":
            return payload
        if status == "error":
            raise PerfectCorpError(
                f"Skin analysis failed: {data.get('error') or data}"
            )

        time.sleep(poll_interval_seconds)

    raise PerfectCorpError(
        f"Skin analysis did not finish within {timeout_seconds} seconds."
    )


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
    return [x for x in output if isinstance(x, dict)]
