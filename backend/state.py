"""
Conversation state management for multi-turn dialogs
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationState:
    user_id: str
    messages: List[Message] = field(default_factory=list)
    pending_action: Optional[Dict] = None
    context: Dict = field(default_factory=dict)
    max_history: int = 10
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.messages.append(Message(role=role, content=content))
        # Keep only last N messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context(self) -> str:
        """Get formatted conversation context for LLM"""
        lines = []
        for msg in self.messages[-5:]:  # Last 5 messages
            prefix = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)
    
    def set_pending_action(self, action_type: str, data: dict):
        """Set action awaiting confirmation"""
        self.pending_action = {
            "type": action_type,
            "data": data,
            "timestamp": datetime.now()
        }
    
    def clear_pending_action(self):
        """Clear pending action"""
        self.pending_action = None
    
    def update_context(self, key: str, value):
        """Update conversation context"""
        self.context[key] = value
