"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
Adapted for Windows environment.
"""

import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast
import asyncio
                
import httpx
from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIResponse,APIResponseValidationError,APIError,APIStatusError
from anthropic.types import (
    ToolResultBlockParam,
    
)
from anthropic.types.beta import (
    BetaContentBlock,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaCacheControlEphemeralParam,
    BetaTextBlock,
    BetaToolUseBlockParam,
    
)
import time

from .tools import ComputerTool, ToolCollection, ToolResult

BETA_FLAG = "computer-use-2024-10-22"
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
}

# System prompt adapted for Windows environment
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilizing a Windows {platform.machine()} system with internet access.
* You have access to mouse and keyboard control through PyAutoGUI.
* You can perform clicks, type text, and take screenshots.
* The system maintains exact monitor resolution for perfect accuracy.
* Screenshots are taken at full monitor resolution and compressed only if needed.
* The system properly accounts for Windows DPI scaling and taskbar position.
* When using your computer function calls, they take a while to run and send back to you. Where possible/feasible, try to chain multiple of these calls all into one function calls request.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* The system maintains exact screen dimensions - no resolution scaling is performed.
* Screenshots are taken at full monitor resolution to maintain perfect accuracy.
* Only compression is applied if needed to stay under size limits.
* The system handles Windows-specific elements like taskbar and DPI scaling.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.Either that, or make sure you scroll up/down using key "pgup" or "pgdn" to see everything before deciding something isn't available.
* carefully evaluate if you have achieved the right outcome. Explicitly show your thinking: "I have evaluated step X..." If not correct, try again. Only when you confirm a step was executed correctly should you move on to the next one.
* Note that you have to click into the browser address bar before typing a URL.
</IMPORTANT>

<COORDINATE_HANDLING>
* Coordinates are maintained at exact screen resolution.
* DPI scaling is properly handled for accurate positioning.
* Taskbar position is accounted for in coordinate calculations.
* The system maintains perfect 1:1 pixel mapping with the screen.
* Coordinate translations preserve exact screen positions.
</COORDINATE_HANDLING>"""

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlockParam], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request, httpx.Response | object | None, Exception | None], None
    ],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
    max_message_pairs: int = 7,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    tool_collection = ToolCollection(
        ComputerTool(),
    )
    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    )

    while True:
        # Trim message history before adding new messages
        if len(messages) > max_message_pairs * 2:
            messages = messages[-max_message_pairs * 2:]

        enable_prompt_caching = False
        betas = [COMPUTER_USE_BETA_FLAG]
        image_truncation_threshold = 10
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key)
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
        
        if enable_prompt_caching:
            betas.append(PROMPT_CACHING_BETA_FLAG)
            _inject_prompt_caching(messages)
            # Is it ever worth it to bust the cache with prompt caching?
            image_truncation_threshold = 20
            system["cache_control"] = {"type": "ephemeral"}

        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=image_truncation_threshold,
            )

        # Call the API
        #to avoid rate limit sleep for a while as cooldown
        time.sleep(2)
        #print("debug",messages)
        #print("debug",tool_collection.to_params())
        try:
            raw_response = client.beta.messages.with_raw_response.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=[system],
                tools=[
                        *tool_collection.to_params(),  # 展開現有的工具列表
        #{  # 添加新的工具
        #    "name": "get_weather",
        #    "description": "Get the current weather in a given location",
        #    "input_schema": {
        #        "type": "object",
        #        "properties": {
        #            "location": {
        #                "type": "string",
        #                "description": "The city and state, e.g. San Francisco, CA"
        #            },
        #            "unit": {
        #                "type": "string",
        #                "enum": ["celsius", "fahrenheit"],
        #                "description": "The unit of temperature, either 'celsius' or 'fahrenheit'"
        #            }
        #        },
        #        "required": ["location"]
        #    }
        #}
                    ],
                betas=betas,
            )
        except (APIStatusError, APIResponseValidationError) as e:
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            api_response_callback(e.request, e.body, e)
            return messages

        api_response_callback(cast(APIResponse[BetaMessage], raw_response))

        response = raw_response.parse()

        messages.append(
            {
                "role": "assistant",
                "content": cast(list[BetaContentBlockParam], response.content),
            }
        )

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in cast(list[BetaContentBlock], response.content):
            output_callback(content_block)
            if content_block.type == "tool_use":
                #add delay to make series of tool_use become better
                time.sleep(1)
                result = await tool_collection.run(
                    name=content_block.name,
                    tool_input=cast(dict[str, Any], content_block.input),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block.id)
                )
                tool_output_callback(result, content_block.id)

        if not tool_result_content:
            return messages

        messages.append({"content": tool_result_content, "role": "user"})


def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int = 10,
):
    """
    With the assumption that images are screenshots that are of diminishing value as
    the conversation progresses, remove all but the final `images_to_keep` tool_result
    images in place, with a chunk of min_removal_threshold to reduce the amount we
    break the implicit prompt cache.
    """
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        list[ToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )
    #計算messages中有多少張圖
    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    images_to_remove = total_images - images_to_keep
    # for better cache behavior, we want to remove in chunks
    images_to_remove -= images_to_remove % min_removal_threshold

    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text


def _response_to_params(
    response: BetaMessage,
) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
    res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            res.append({"type": "text", "text": block.text})
        else:
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res


def _inject_prompt_caching(
    messages: list[BetaMessageParam],
):
    """
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
    """

    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(
            content := message["content"], list
        ):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                    {"type": "ephemeral"}
                )
            else:
                content[-1].pop("cache_control", None)
                # we'll only every have one extra turn per loop
                break


