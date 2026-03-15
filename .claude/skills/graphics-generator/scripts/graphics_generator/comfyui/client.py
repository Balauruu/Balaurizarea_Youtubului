"""ComfyUI REST client — queue prompts, poll history, download images.

Uses HTTP polling instead of websockets to avoid extra dependencies.
Raises ComfyUIUnavailableError on connection failures with actionable messages.
"""

import time
from pathlib import Path
from typing import Any

import requests


class ComfyUIUnavailableError(Exception):
    """Raised when the ComfyUI server cannot be reached."""


class ComfyUIClient:
    """Thin REST client for the ComfyUI prompt queue API.

    Args:
        host: ComfyUI server hostname (default: 127.0.0.1).
        port: ComfyUI server port (default: 8188).
        timeout: HTTP request timeout in seconds (default: 30).
        poll_interval: Seconds between history polls (default: 2.0).
        max_poll_attempts: Maximum poll iterations before giving up (default: 150).
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        timeout: int = 30,
        poll_interval: float = 2.0,
        max_poll_attempts: int = 150,
    ) -> None:
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts

    @property
    def address(self) -> str:
        """Human-readable server address for error messages."""
        return f"{self.host}:{self.port}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if the ComfyUI server is reachable."""
        try:
            resp = requests.get(
                f"{self.base_url}/system_stats",
                timeout=5,
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def queue_prompt(self, workflow_json: dict) -> str:
        """Submit a workflow to the ComfyUI prompt queue.

        Args:
            workflow_json: ComfyUI API-format workflow dict (nodes keyed by ID).

        Returns:
            The prompt_id assigned by ComfyUI.

        Raises:
            ComfyUIUnavailableError: If the server is unreachable.
        """
        payload = {"prompt": workflow_json}
        try:
            resp = requests.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["prompt_id"]
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise ComfyUIUnavailableError(
                f"Cannot connect to ComfyUI at {self.address}: {exc}. "
                f"Use --code-gen-only to skip ComfyUI blocks."
            ) from exc

    def poll_history(self, prompt_id: str) -> dict[str, Any]:
        """Poll GET /history/{prompt_id} until the job completes.

        Returns:
            The outputs dict from the completed history entry.

        Raises:
            ComfyUIUnavailableError: If the server is unreachable.
            TimeoutError: If polling exceeds max_poll_attempts.
        """
        url = f"{self.base_url}/history/{prompt_id}"
        for attempt in range(self.max_poll_attempts):
            try:
                resp = requests.get(url, timeout=self.timeout)
                resp.raise_for_status()
            except (requests.ConnectionError, requests.Timeout) as exc:
                raise ComfyUIUnavailableError(
                    f"Lost connection to ComfyUI at {self.address} while polling "
                    f"prompt {prompt_id}: {exc}"
                ) from exc

            data = resp.json()
            if prompt_id in data:
                entry = data[prompt_id]
                status = entry.get("status", {})
                if status.get("completed", False) or status.get("status_str") == "success":
                    return entry.get("outputs", {})
                # Check for error status
                if status.get("status_str") == "error":
                    raise RuntimeError(
                        f"ComfyUI prompt {prompt_id} failed: {status}"
                    )

            time.sleep(self.poll_interval)

        raise TimeoutError(
            f"ComfyUI prompt {prompt_id} did not complete after "
            f"{self.max_poll_attempts} poll attempts ({self.address})"
        )

    def download_image(
        self,
        filename: str,
        subfolder: str,
        output_dir: Path,
    ) -> Path:
        """Download a generated image from ComfyUI's /view endpoint.

        Args:
            filename: The filename returned in history outputs.
            subfolder: The subfolder returned in history outputs.
            output_dir: Local directory to save the file to.

        Returns:
            Path to the downloaded file.

        Raises:
            ComfyUIUnavailableError: If the server is unreachable.
        """
        params = {"filename": filename, "subfolder": subfolder, "type": "output"}
        try:
            resp = requests.get(
                f"{self.base_url}/view",
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise ComfyUIUnavailableError(
                f"Cannot download image from ComfyUI at {self.address}: {exc}"
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        dest = output_dir / filename
        dest.write_bytes(resp.content)
        return dest
