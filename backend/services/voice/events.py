from pydantic import BaseModel


class VoiceAgentEvent(BaseModel):
    """Base event for the voice agent pipeline."""
    type: str
    session_id: str | None = None


class CallStartedEvent(VoiceAgentEvent):
    """Synthetic event emitted immediately when a call connects, to kick off the pipeline."""

    @classmethod
    def create(cls, session_id: str | None = None):
        return cls(type="call_started", session_id=session_id)


class STTChunkEvent(VoiceAgentEvent):
    """Interim STT result."""
    transcript: str

    @classmethod
    def create(cls, transcript: str):
        return cls(type="stt_chunk", transcript=transcript)


class STTOutputEvent(VoiceAgentEvent):
    """Final STT result — complete user utterance."""
    transcript: str

    @classmethod
    def create(cls, transcript: str):
        return cls(type="stt_output", transcript=transcript)


class AgentChunkEvent(VoiceAgentEvent):
    """A sentence chunk from the LLM agent, ready for TTS."""
    text: str
    turn_id: int | None = None

    @classmethod
    def create(cls, text: str, turn_id: int | None = None):
        return cls(type="agent_chunk", text=text, turn_id=turn_id)


class BargeInEvent(VoiceAgentEvent):
    """User interrupted the agent (barge-in detected)."""

    @classmethod
    def create(cls):
        return cls(type="barge_in")


class TTSChunkEvent(VoiceAgentEvent):
    """Audio bytes from TTS synthesis."""
    audio: bytes
    turn_id: int | None = None

    @classmethod
    def create(cls, audio: bytes, turn_id: int | None = None):
        return cls(type="tts_chunk", audio=audio, turn_id=turn_id)


class HangupEvent(VoiceAgentEvent):
    """Agent explicitly requested to hang up the call."""
    reason: str | None = None

    @classmethod
    def create(cls, reason: str = "agent_ended_call"):
        return cls(type="hangup", reason=reason)

class FillerAudioEvent(VoiceAgentEvent):
    """Event to trigger instant filler audio for TTFB masking."""
    
    @classmethod
    def create(cls):
        return cls(type="filler_audio")

class AgentEndEvent(VoiceAgentEvent):
    """Signals that the LLM has finished the full response for this turn."""
    @classmethod
    def create(cls):
        return cls(type="agent_end")
