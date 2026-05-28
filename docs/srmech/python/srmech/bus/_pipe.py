"""Daemon-pipe utility composing two srmech.bus endpoints.

The :func:`pipe` helper subscribes to a source endpoint and re-sends
every broadcast event to a sink endpoint (optionally via a
``transform`` callable). Useful for chaining multi-stage sweeps where
one process emits, a transformation process re-shapes, and a
consumer process subscribes downstream.

Framework reading: the pipe IS a Class M ∘ Class F operator
composition (cross-class bind + render/transform) across two
substrate-class-instance endpoints.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from ._client import Channel, connect

logger = logging.getLogger("srmech.bus.pipe")

Transform = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]


class _PipeHandle:
    """Handle returned by :func:`pipe` — controls the running daemon."""

    def __init__(
        self,
        source_name: str,
        sink_name: str,
        thread: threading.Thread,
        stop_event: threading.Event,
    ) -> None:
        self.source_name = source_name
        self.sink_name = sink_name
        self._thread = thread
        self._stop_event = stop_event

    def stop(self, *, timeout: float = 2.0) -> None:
        """Signal the daemon to stop; join the thread."""
        self._stop_event.set()
        self._thread.join(timeout=timeout)

    @property
    def alive(self) -> bool:
        return self._thread.is_alive()


def pipe(
    source: str,
    sink: str,
    *,
    transform: Optional[Transform] = None,
    background: bool = True,
) -> _PipeHandle:
    """Subscribe to ``source``; forward each broadcast event to ``sink``.

    Parameters
    ----------
    source
        Endpoint name to subscribe to (broadcast consumer side).
    sink
        Endpoint name to forward events into (req/rep send side;
        ``expect_reply=False``).
    transform
        Optional callable that takes one event dict and returns the
        dict to send to the sink (or ``None`` to drop the event).
    background
        If True (default), run the forwarding loop in a daemon
        thread and return a :class:`_PipeHandle` immediately. If
        False, block in the foreground until the source channel
        closes.

    Returns
    -------
    _PipeHandle
        Handle for stopping the daemon (only meaningful when
        ``background=True``; otherwise ``stop()`` is a no-op since
        the call already returned).
    """
    stop_event = threading.Event()

    def _loop() -> None:
        try:
            with connect(source) as src_ch, connect(sink) as sink_ch:
                for ev in src_ch.subscribe(timeout=0.5):
                    if stop_event.is_set():
                        return
                    out = ev
                    if transform is not None:
                        try:
                            out = transform(ev)
                        except Exception:
                            logger.exception(
                                "transform raised; dropping event"
                            )
                            continue
                        if out is None:
                            continue
                    sink_event = {
                        "type": out.get("type", ev.get("type", "_piped")),
                        "payload": out.get("payload", {}),
                    }
                    try:
                        sink_ch.send(sink_event, expect_reply=False)
                    except Exception:
                        logger.exception(
                            "sink send failed; bailing pipe loop"
                        )
                        return
        except Exception:
            logger.exception("pipe loop crashed")

    if background:
        th = threading.Thread(
            target=_loop,
            name=f"srmech-bus-pipe-{source}->{sink}",
            daemon=True,
        )
        th.start()
        return _PipeHandle(source, sink, th, stop_event)
    # Foreground: run synchronously, return a finished handle.
    _loop()
    finished = threading.Thread(target=lambda: None)
    finished.start()
    finished.join()
    return _PipeHandle(source, sink, finished, stop_event)


__all__ = ["pipe", "_PipeHandle"]
