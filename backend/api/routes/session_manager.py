# # Simple in-memory session manager for call flows

# class SessionManager:
#     def __init__(self):
#         # Stores sessions as {call_sid: current_step_index}
#         self.sessions = {}

#     def get_step_index(self, call_sid):
#         """Get the current step index for a call_sid. Returns 0 if not found."""
#         return self.sessions.get(call_sid, 0)

#     def update_step_index(self, call_sid, step_index):
#         """Update the current step index for a call_sid."""
#         self.sessions[call_sid] = step_index

#     def clear_session(self, call_sid):
#         """Remove a session when the call is complete or expired."""
#         if call_sid in self.sessions:
#             del self.sessions[call_sid]

class SessionManager:
    def __init__(self):
        # Stores sessions as {call_sid: current_step_index}
        self.sessions = {}
        # Stores retry count as {call_sid: retry_count}
        self.retry_counts = {}

    def get_step_index(self, call_sid):
        """Get the current step index for a call_sid. Returns 0 if not found."""
        return self.sessions.get(call_sid, 0)

    def update_step_index(self, call_sid, step_index):
        """Update the current step index for a call_sid."""
        self.sessions[call_sid] = step_index

    def get_retry_count(self, call_sid):
        """Get the current retry count for a call_sid. Returns 0 if not found."""
        return self.retry_counts.get(call_sid, 0)

    def increment_retry(self, call_sid):
        """Increment retry count for a call_sid."""
        current = self.retry_counts.get(call_sid, 0)
        self.retry_counts[call_sid] = current + 1
        return self.retry_counts[call_sid]

    def reset_retry(self, call_sid):
        """Reset retry count to 0 when user provides valid answer."""
        self.retry_counts[call_sid] = 0

    def clear_session(self, call_sid):
        """Remove a session when the call is complete or expired."""
        if call_sid in self.sessions:
            del self.sessions[call_sid]
        if call_sid in self.retry_counts:
            del self.retry_counts[call_sid]