import requests
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class SuccessResponseDataFormat:
    total_llm_calls: int
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    final_llm_response: Dict[str, Any]
    llm_responses_arr: List[Dict[str, Any]]
    messages: List[str]
    output_type: str

@dataclass
class LlmResponseStruct:
    Data: Optional[Dict[str, Any]]
    Error: Optional[Union[Exception, str, Dict[str, Any]]]
    Status: bool

@dataclass
class AzureAndOpenAiChatCompletionParams:
    input: str = ''
    images_arr: List[Any] = field(default_factory=list)
    input_type: str = 'text'
    is_stream: bool = False
    prompt: str = ''
    api_key: str = ''
    chat_model: str = ''
    vision_model: str = ''
    speech_model: str = ''
    speech_to_text: str = ''
    chat_history: List[ChatMessage] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    temperature: float = 0.1
    max_tokens: int = 1000
    forced_tool_calls: Optional[Any] = None
    tool_choice: str = 'auto'

async def openai_processor(data: Dict[str, Any]) -> LlmResponseStruct:
    """ 
    Main OpenAI Processor function
    """
    try:
        # Parse and validate input parameters
        params = AzureAndOpenAiChatCompletionParams(
            input=data.get('input', ''),
            images_arr=data.get('images_arr', []),
            input_type=data.get('input_type', 'text'),
            is_stream=data.get('is_stream', False),
            prompt=data.get('prompt', ''),
            api_key=data.get('api_key', ''),
            chat_model=data.get('chat_model', ''),
            vision_model=data.get('vision_model', ''),
            speech_model=data.get('speech_model', ''),
            speech_to_text=data.get('speech_to_text', ''),
            chat_history=[ChatMessage(**msg) if isinstance(msg, dict) else msg 
                         for msg in data.get('chat_history', [])],
            tools=data.get('tools', []),
            temperature=data.get('temperature', 0.1),
            max_tokens=data.get('max_tokens', 1000),
            forced_tool_calls=data.get('forced_tool_calls'),
            tool_choice=data.get('tool_choice', 'auto')
        )

        # Determine model
        selected_model = params.chat_model
        if params.input_type == 'image':
            selected_model = params.vision_model
        elif params.input_type == 'audio':
            selected_model = params.speech_model

        # Basic validation
        if not params.api_key:
            return LlmResponseStruct(Data=None, Error=Exception("OpenAI API Key is required"), Status=False)
        if params.max_tokens <= 0:
            return LlmResponseStruct(Data=None, Error=Exception("Max tokens must be > 0"), Status=False)

        # Build messages array
        messages_arr = [{"role": "system", "content": params.prompt}]
        messages_arr += [{"role": m.role, "content": m.content} for m in params.chat_history]

        # Prepare request payload
        payload = {
            "model": selected_model,
            "messages": messages_arr,
            "max_tokens": params.max_tokens,
            "stream": False,
            "tools": params.tools,
            "tool_choice": params.tool_choice,
            "temperature": params.temperature,
        }
        
        # print(f"payload: {payload}")

        # Send request
        url = f"https://api.openai.com/v1/chat/completions"
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {params.api_key}'}

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        response_data = resp.json()

        # Detect tool calls
        choices = response_data.get('choices', [])
        first_msg = choices[0].get('message', {}) if choices else {}
        tool_calls = first_msg.get('tool_calls') or []
        is_tool_call = len(tool_calls) > 0

        # Usage metrics
        usage = response_data.get('usage', {})
        message_content = first_msg.get('content', '')

        final_format = SuccessResponseDataFormat(
            total_llm_calls=1,
            total_tokens=usage.get('total_tokens', 0),
            total_input_tokens=usage.get('prompt_tokens', 0),
            total_output_tokens=usage.get('completion_tokens', 0),
            final_llm_response=response_data,
            llm_responses_arr=[response_data],
            messages=[message_content],
            output_type="tool_call" if is_tool_call else "text"
        )
        
        # print(f"response: {final_format}")

        # Return as dict to avoid subscript errors
        return LlmResponseStruct(Data=asdict(final_format), Error=None, Status=True)

    except requests.exceptions.RequestException as req_err:
        err_data = None
        if hasattr(req_err, 'response') and req_err.response is not None:
            try:
                err_data = req_err.response.json()
            except ValueError:
                err_data = req_err.response.text
        else:
            err_data = str(req_err)
        return LlmResponseStruct(Data=None, Error=err_data, Status=False)

    except Exception as err:
        return LlmResponseStruct(Data=None, Error=err, Status=False)
