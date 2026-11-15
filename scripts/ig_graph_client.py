#!/usr/bin/env python3
"""Official Meta Instagram Graph API client for @cyberjasoos Reels, insights, and poll ops."""

import json, os, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

DEFAULT_IG_HOST, DEFAULT_FB_HOST, DEFAULT_API_VERSION = "https://graph.instagram.com", "https://graph.facebook.com", "v22.0"
PRIMARY_INSIGHT_METRICS = "views,reach,saved,shares,likes,comments,reels_skip_rate"
FALLBACK_INSIGHT_METRICS = "views,reach,saved,shares,likes,comments"


class GraphAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: object = None) -> None:
        super().__init__(message)
        self.status_code, self.payload = status_code, payload


class InstagramGraphClient:
    """Stdlib-only official Instagram Graph API client with rolling rate-limit & burst guards."""

    def __init__(
        self, access_token: str | None = None, ig_user_id: str | None = None, api_host: str | None = None,
        api_version: str | None = None, urlopen_fn=None, sleep_fn=None, time_fn=None,
        max_calls_per_hour: int = 180, min_reply_interval_sec: float = 2.2,
    ) -> None:
        raw_tok = access_token if access_token is not None else os.environ.get("IG_ACCESS_TOKEN", "")
        raw_uid = ig_user_id if ig_user_id is not None else os.environ.get("IG_USER_ID", "")
        self.access_token, self.ig_user_id = raw_tok.strip(), raw_uid.strip()
        env_host = os.environ.get("IG_API_HOST", "").strip()
        fallback_host = DEFAULT_FB_HOST if os.environ.get("IG_USE_FB_GRAPH", "").strip() == "1" else DEFAULT_IG_HOST
        self.api_host = (api_host or env_host or fallback_host).rstrip("/")
        self.api_version = (api_version or os.environ.get("IG_API_VERSION", DEFAULT_API_VERSION)).strip().strip("/")
        self.urlopen_fn = urlopen_fn or urllib.request.urlopen
        self.sleep_fn = sleep_fn or time.sleep
        self.time_fn = time_fn or time.monotonic
        self.max_calls_per_hour = int(max_calls_per_hour)
        self.min_reply_interval_sec = float(min_reply_interval_sec)
        self._call_timestamps: list[float] = []
        self._last_reply_ts: float | None = None

    def _redact(self, text: str) -> str:
        return text.replace(self.access_token, "[REDACTED]") if self.access_token and self.access_token in text else text

    def _require_token(self) -> str:
        if not self.access_token:
            raise ValueError("Missing IG_ACCESS_TOKEN in environment or InstagramGraphClient.")
        return self.access_token

    def _require_user_id(self) -> str:
        if not self.ig_user_id:
            raise ValueError("Missing IG_USER_ID in environment or InstagramGraphClient.")
        return self.ig_user_id

    @property
    def calls_in_last_hour(self) -> int:
        cutoff = self.time_fn() - 3600.0
        self._call_timestamps = [ts for ts in self._call_timestamps if ts > cutoff]
        return len(self._call_timestamps)

    def _record_call(self) -> None:
        if self.calls_in_last_hour >= self.max_calls_per_hour:
            raise RuntimeError(f"Rate-limit safety ceiling reached ({self.max_calls_per_hour}/hr); halting below 200/hr.")
        self._call_timestamps.append(self.time_fn())

    def _send_http(
        self, method: str, url: str, headers: dict[str, str], body: bytes | None = None, timeout: float = 30.0
    ) -> dict:
        self._record_call()
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            raw_resp = self.urlopen_fn(req, timeout=timeout) if self.urlopen_fn is urllib.request.urlopen else self.urlopen_fn(req)
            if hasattr(raw_resp, "__enter__"):
                with raw_resp as resp:
                    raw_bytes = resp.read()
            else:
                raw_bytes = raw_resp.read()
        except urllib.error.HTTPError as exc:
            err_raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            safe_err, safe_url = self._redact(err_raw), self._redact(url)
            try:
                parsed_err = json.loads(safe_err)
            except ValueError:
                parsed_err = safe_err
            raise GraphAPIError(exc.code, f"Graph API HTTP {exc.code} on {method} {safe_url}: {safe_err}", parsed_err) from None
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Graph API network error on {method} {self._redact(url)}: {self._redact(str(exc))}") from None
        if not raw_bytes:
            return {}
        decoded = raw_bytes.decode("utf-8") if isinstance(raw_bytes, (bytes, bytearray)) else str(raw_bytes)
        return json.loads(decoded) if decoded.strip() else {}

    def _request(
        self, method: str, path_or_url: str, params: dict[str, object] | None = None,
        payload: dict[str, object] | None = None, base_host: str | None = None,
    ) -> dict:
        token = self._require_token()
        if path_or_url.startswith(("http://", "https://")):
            url = path_or_url
        else:
            url = f"{(base_host or self.api_host).rstrip('/')}/{self.api_version}/{path_or_url.lstrip('/')}"
        if params:
            url = f"{url}{'&' if '?' in url else '?'}{urllib.parse.urlencode(params)}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        body = None
        if payload is not None:
            body, headers["Content-Type"] = json.dumps(payload).encode("utf-8"), "application/json"
        return self._send_http(method, url, headers=headers, body=body)

    def get_profile(self) -> dict:
        uid = self._require_user_id()
        return self._request("GET", f"/{uid}", params={"fields": "id,username,name,followers_count,media_count"})

    def list_recent_media(self, limit: int = 10) -> list[dict]:
        uid = self._require_user_id()
        fields = "id,caption,media_type,permalink,timestamp,like_count,comments_count"
        res = self._request("GET", f"/{uid}/media", params={"fields": fields, "limit": int(limit)})
        return list(res.get("data") or [])

    def get_media_insights(self, media_id: str) -> dict:
        try:
            res = self._request("GET", f"/{media_id}/insights", params={"metric": PRIMARY_INSIGHT_METRICS})
        except GraphAPIError as err:
            if err.status_code != 400:
                raise
            res = self._request("GET", f"/{media_id}/insights", params={"metric": FALLBACK_INSIGHT_METRICS})
        metrics: dict[str, int | float] = {}
        for item in res.get("data") or []:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            vals = item.get("values")
            if isinstance(vals, list) and vals and isinstance(vals[0], dict):
                val = vals[0].get("value")
            elif isinstance(item.get("total_value"), dict):
                val = item["total_value"].get("value")
            else:
                val = item.get("value")
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                metrics[str(item["name"])] = val
        out: dict[str, object] = {"media_id": media_id, **metrics}
        reach = float(metrics.get("reach", 0) or 0)
        if reach > 0:
            out["save_rate_pct"] = round((float(metrics.get("saved", 0) or 0) / reach) * 100.0, 2)
            out["share_rate_pct"] = round((float(metrics.get("shares", 0) or 0) / reach) * 100.0, 2)
        return out

    def fetch_all_comments(self, media_id: str, max_pages: int = 10) -> list[dict]:
        collected: list[dict] = []
        next_target: str | None = f"/{media_id}/comments"
        params: dict[str, object] | None = {"fields": "id,text,username,timestamp,like_count", "limit": 50}
        for _ in range(max(1, int(max_pages))):
            if not next_target:
                break
            res = self._request("GET", next_target, params=params)
            params = None
            batch = [c for c in (res.get("data") or []) if isinstance(c, dict)]
            collected.extend(batch)
            next_target = ((res.get("paging") or {}).get("next") or "").strip() or None
            if not batch:
                break
        return collected

    def post_comment(self, media_id: str, message: str) -> dict:
        msg = message.strip()
        if not msg:
            raise ValueError("Comment message must be non-empty.")
        return self._request("POST", f"/{media_id}/comments", payload={"message": msg})

    def reply_to_comment(self, comment_id: str, message: str) -> dict:
        msg = message.strip()
        if not msg:
            raise ValueError("Reply message must be non-empty.")
        if self._last_reply_ts is not None and self.min_reply_interval_sec > 0:
            elapsed = self.time_fn() - self._last_reply_ts
            if elapsed < self.min_reply_interval_sec:
                self.sleep_fn(self.min_reply_interval_sec - elapsed)
        res = self._request("POST", f"/{comment_id}/replies", payload={"message": msg})
        self._last_reply_ts = self.time_fn()
        return res

    def publish_reel_resumable(
        self, mp4_path: Path, caption: str, share_to_feed: bool = True,
        thumb_offset_ms: int = 0, poll_interval_sec: float = 12.0, max_polls: int = 20,
    ) -> dict:
        token, uid, video_file = self._require_token(), self._require_user_id(), Path(mp4_path)
        if not video_file.is_file() or video_file.stat().st_size <= 0:
            raise FileNotFoundError(f"MP4 file missing or empty: {video_file}")
        mp4_bytes = video_file.read_bytes()
        init_payload = {
            "media_type": "REELS", "upload_type": "resumable", "caption": caption,
            "share_to_feed": bool(share_to_feed), "thumb_offset": int(thumb_offset_ms),
        }
        init_res = self._request("POST", f"/{uid}/media", payload=init_payload, base_host=DEFAULT_FB_HOST)
        container_id, upload_uri = str(init_res.get("id") or "").strip(), str(init_res.get("uri") or "").strip()
        if not container_id or not upload_uri:
            raise RuntimeError(f"Resumable session missing container id/uri: {init_res}")
        up_headers = {
            "Authorization": f"OAuth {token}", "offset": "0",
            "file_size": str(len(mp4_bytes)), "Content-Type": "application/octet-stream",
        }
        upload_res = self._send_http("POST", upload_uri, headers=up_headers, body=mp4_bytes, timeout=300.0)
        last_code = ""
        for attempt in range(max(1, int(max_polls))):
            st = self._request("GET", f"/{container_id}", params={"fields": "status_code,status"})
            last_code = str(st.get("status_code") or "").upper()
            if last_code == "FINISHED":
                break
            if last_code in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Reel container {container_id} failed ({last_code}): {st.get('status', '')}")
            if attempt + 1 < max_polls:
                self.sleep_fn(poll_interval_sec)
        else:
            raise RuntimeError(f"Reel container {container_id} timed out after {max_polls} polls (last={last_code!r}).")
        pub = self._request("POST", f"/{uid}/media_publish", payload={"creation_id": container_id})
        return {"id": pub.get("id"), "media_id": pub.get("id"), "container_id": container_id, "upload": upload_res}
