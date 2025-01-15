import json
from typing import Any, Dict


class ChatMessageUtils:
    @staticmethod
    def add_strategy_id_to_message(
        message: Dict[str, Any], tool_call_id: str, strategy_id: int
    ) -> Dict[str, Any]:
        """Add strategy ID to a specific tool invocation result in a message."""
        if not message.get("toolInvocations"):
            return message

        for invocation in message["toolInvocations"]:
            if invocation.get("toolCallId") == tool_call_id and "result" in invocation:
                try:
                    result_data = json.loads(invocation["result"])
                    result_data["strategy_id"] = strategy_id
                    invocation["result"] = json.dumps(result_data)
                except json.JSONDecodeError:
                    continue

        return message

    @staticmethod
    def remove_strategy_id_from_message(
        message: Dict[str, Any], strategy_id: int
    ) -> Dict[str, Any]:
        """Remove strategy ID from all tool invocation results in a message."""
        if not message.get("toolInvocations"):
            return message

        for invocation in message["toolInvocations"]:
            if "result" in invocation:
                try:
                    result_data = json.loads(invocation["result"])
                    if result_data.get("strategy_id") == strategy_id:
                        del result_data["strategy_id"]
                        invocation["result"] = json.dumps(result_data)
                except json.JSONDecodeError:
                    continue

        return message
