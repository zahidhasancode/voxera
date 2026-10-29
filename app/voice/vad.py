"""Energy-based voice activity detection for fast barge-in.

Barge-in used to wait for the recogniser's first partial transcript, which takes
several hundred milliseconds. This detector looks at the raw inbound audio
instead: a few consecutive frames clearly louder than the background noise count
as the caller starting to talk. It learns the noise floor from quiet frames, so a
steady background (a fan, street noise) does not trigger it.

Limit: it hears loudness, not words. It relies on the client's echo cancellation
(browsers provide it) to keep the agent's own voice out of the microphone. Phone
calls have no echo cancellation here, so the telephony bridge does not use it.
"""

from __future__ import annotations

from app.voice.audio import pcm_frame_energy


class EnergyVAD:
    """Detects the start of speech from PCM16 frames."""

    def __init__(
        self,
        *,
        min_energy: float = 500.0,
        noise_ratio: float = 3.0,
        speech_frames: int = 3,
        noise_alpha: float = 0.05,
        initial_noise: float = 100.0,
    ) -> None:
        self.min_energy = min_energy
        self.noise_ratio = noise_ratio
        self.speech_frames = speech_frames
        self.noise_alpha = noise_alpha
        self.noise_floor = initial_noise
        self._run = 0
        self._in_speech = False

    @property
    def threshold(self) -> float:
        return max(self.min_energy, self.noise_floor * self.noise_ratio)

    def update(self, frame: bytes) -> bool:
        """Feed one frame. Returns True exactly once when speech starts."""
        energy = pcm_frame_energy(frame)
        if energy >= self.threshold:
            self._run += 1
            if not self._in_speech and self._run >= self.speech_frames:
                self._in_speech = True
                return True
            return False
        # Quiet frame: it belongs to the background, so it updates the noise estimate.
        self._run = 0
        self._in_speech = False
        self.noise_floor += self.noise_alpha * (energy - self.noise_floor)
        return False

    def reset(self) -> None:
        self._run = 0
        self._in_speech = False
