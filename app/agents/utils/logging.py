from typing import Any, Dict, Optional
from app.util.logger import setup_logger

logger = setup_logger("agents")


def log_agent_step(
    agent_name: str,
    step_name: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    error: Optional[Exception] = None,
) -> None:
    """
    Log an AI agent step with input and output data.

    Args:
        agent_name: Name of the agent (e.g., 'strategy_generator', 'backtest_analyzer')
        step_name: Name of the step being executed
        input_data: Optional dictionary containing input data
        output_data: Optional dictionary containing output data
        error: Optional exception if the step failed
    """
    log_data = {
        "agent": agent_name,
        "step": step_name,
    }

    if input_data:
        log_data["input"] = input_data
    if output_data:
        log_data["output"] = output_data
    if error:
        log_data["error"] = str(error)
        log_data["error_type"] = type(error).__name__

    if error:
        logger.error(
            f"Agent {agent_name} failed at step {step_name}", extra={"data": log_data}
        )
    else:
        logger.info(
            f"Agent {agent_name} completed step {step_name}", extra={"data": log_data}
        )


def log_agent_prompt(
    agent_name: str,
    prompt_name: str,
    prompt_template: str,
    prompt_variables: Dict[str, Any],
) -> None:
    """
    Log an AI agent prompt before it's sent to the model.

    Args:
        agent_name: Name of the agent
        prompt_name: Name/identifier of the prompt
        prompt_template: The template string used for the prompt
        prompt_variables: Variables used to fill the prompt template
    """
    logger.debug(
        f"Agent {agent_name} preparing prompt {prompt_name}",
        extra={
            "data": {
                "agent": agent_name,
                "prompt_name": prompt_name,
                "prompt_template": prompt_template,
                "prompt_variables": prompt_variables,
            }
        },
    )


def log_agent_response(
    agent_name: str,
    prompt_name: str,
    response: str,
    tokens_used: Optional[Dict[str, int]] = None,
) -> None:
    """
    Log an AI agent's response from the model.

    Args:
        agent_name: Name of the agent
        prompt_name: Name/identifier of the prompt that generated this response
        response: The model's response text
        tokens_used: Optional dictionary containing token usage statistics
    """
    log_data = {
        "agent": agent_name,
        "prompt_name": prompt_name,
        "response_length": len(response),
    }

    if tokens_used:
        log_data["tokens"] = tokens_used

    logger.debug(
        f"Agent {agent_name} received response for prompt {prompt_name}",
        extra={"data": log_data},
    )


def log_agent_tool_call(
    agent_name: str,
    tool_name: str,
    inputs: Dict[str, Any],
    outputs: Optional[Dict[str, Any]] = None,
    error: Optional[Exception] = None,
) -> None:
    """
    Log an AI agent's tool usage.

    Args:
        agent_name: Name of the agent
        tool_name: Name of the tool being used
        inputs: Dictionary of input parameters to the tool
        outputs: Optional dictionary of tool outputs
        error: Optional exception if the tool call failed
    """
    log_data = {"agent": agent_name, "tool": tool_name, "inputs": inputs}

    if outputs:
        log_data["outputs"] = outputs
    if error:
        log_data["error"] = str(error)
        log_data["error_type"] = type(error).__name__

    if error:
        logger.error(
            f"Agent {agent_name} tool {tool_name} failed", extra={"data": log_data}
        )
    else:
        logger.info(
            f"Agent {agent_name} used tool {tool_name}", extra={"data": log_data}
        )
