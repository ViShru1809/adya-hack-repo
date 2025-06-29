import json
import logging
from typing import Any, Dict, List, Optional

# Assuming these are your imported modules/classes for MCP clients and Azure LLM calls
from src.llm.azureopenai import azure_openai_processor  # your async LLM call function
from src.llm.openai import openai_processor  # your async LLM call function
from src.server_connection import MCPServers  # MCP clients dict or class with call_tool method
from src.llm.gemini import gemini_processor 


class ClientAndServerExecutionResponse:
    def __init__(self):
        self.Data = {
            "total_llm_calls": 0,
            "total_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "final_llm_response": None,
            "llm_responses_arr": [],
            "messages": [],
            "output_type": "text",
            "executed_tool_calls": []
        }
        self.Error: Optional[str] = None
        self.Status: bool = False


async def client_and_server_execution(payload: Dict[str, Any], streaming_callback: Optional[Any] = None) -> ClientAndServerExecutionResponse:
    try:
        result = ClientAndServerExecutionResponse()

        selected_server_credentials = payload.get("selected_server_credentials")
        client_details = payload.get("client_details", {})
        selected_client = payload.get("selected_client", "")
        selected_servers = payload.get("selected_servers", [])
        selected_server = selected_servers[0] if selected_servers else ""

        # Prepare chat history
        input_content = client_details.get("input", "")
        if "chat_history" in client_details:
            client_details["chat_history"].append({"role": "user", "content": input_content})
        else:
            client_details["chat_history"] = [{"role": "user", "content": input_content}]

        temp_tools = json.dumps(client_details.get("tools", []))
        temp_prompt = client_details.get("prompt", "")

        # Extract tool call details for prompt
        tool_call_details_arr = []
        for tool in client_details.get("tools", []):
            tool_call_details_arr.append({
                "function_name": tool.get("function", {}).get("name", ""),
                "function_description": tool.get("function", {}).get("description", ""),
            })

        tools_getting_agent_prompt = f"""
        You are an {selected_server} AI assistant that analyzes user requests and determines the require tool calls from available tools.
        Available tools: {json.dumps(tool_call_details_arr)}
        Analyze each request to determine if it matches available tool capabilities or needs clarification.
        Return TRUE for tool calls when the request clearly maps to available tools without checking the required parameters.
        Return FALSE when the request is ambiguous, missing parameters, or requires more information.
        Output format:
            <function_call>TRUE/FALSE</function_call>
            <selected_tools>function_name1,function_name2 or "none"</selected_tools>
        Use exact tool names from available tools. List all relevant tools ordered by relevance.
        """

        client_details["prompt"] = tools_getting_agent_prompt
        client_details["tools"] = []

        if selected_client == "MCP_CLIENT_AZURE_AI":

            # Initial LLM call
            initial_llm_response = await azure_openai_processor(client_details)
            if not initial_llm_response.Status:
                result.Error = initial_llm_response.Error
                result.Status = initial_llm_response.Status
                return result
            extracted_result = extract_data_from_response(initial_llm_response.Data.get("messages", [{}])[0] if initial_llm_response.Data else "")
            
            result.Data["total_llm_calls"] += 1
            result.Data["total_tokens"] += initial_llm_response.Data.get("total_tokens", 0)
            result.Data["total_input_tokens"] += initial_llm_response.Data.get("total_input_tokens", 0)
            result.Data["total_output_tokens"] += initial_llm_response.Data.get("total_output_tokens", 0)
            result.Data["final_llm_response"] = initial_llm_response.Data.get("final_llm_response")
            result.Data["llm_responses_arr"].append(initial_llm_response.Data.get("final_llm_response"))

            if streaming_callback and streaming_callback.get("is_stream"):
                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                    "Data": "Optimized Token LLM call Successfully Completed",
                    "Error": None,
                    "Status": True,
                    "StreamingStatus": "IN-PROGRESS",
                    "Action": "NOTIFICATION"
                }))
            
            if extracted_result["isFunctionCall"]:
                final_tool_calls = []
                selected_tools = extracted_result["selectedTools"]
                parsed_tools = json.loads(temp_tools)

                for tool_name in selected_tools:
                    matching_tool = next((t for t in parsed_tools if t.get("function", {}).get("name") == tool_name), None)
                    if matching_tool:
                        final_tool_calls.append(matching_tool)

                client_details["prompt"] = temp_prompt
                client_details["tools"] = final_tool_calls
                

                # Loop to handle multiple LLM calls and tool executions
                while True:
                    response = await azure_openai_processor(client_details)
                    if not response.Status:
                        result.Error = response.Error
                        result.Status = response.Status
                        return result

                    result.Data["total_llm_calls"] += 1
                    result.Data["total_tokens"] += response.Data.get("total_tokens", 0)
                    result.Data["total_input_tokens"] += response.Data.get("total_input_tokens", 0)
                    result.Data["total_output_tokens"] += response.Data.get("total_output_tokens", 0)
                    result.Data["final_llm_response"] = response.Data.get("final_llm_response")
                    result.Data["llm_responses_arr"].append(response.Data.get("final_llm_response"))

                    if response.Data.get("output_type") == "text":
                        result.Data["messages"].extend(response.Data.get("messages", []))
                        result.Data["output_type"] = response.Data.get("output_type", "")
                        result.Error = response.Error
                        result.Status = response.Status

                        for message in response.Data.get("messages", []):
                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": message,
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "MESSAGE"
                                }))
                        return result

                    if streaming_callback and streaming_callback.get("is_stream"):
                        await streaming_callback["streamCallbacks"].on_data(json.dumps({
                            "Data": "Tool Calls Started",
                            "Error": None,
                            "Status": True,
                            "StreamingStatus": "IN-PROGRESS",
                            "Action": "NOTIFICATION"
                        }))

                    for tool in response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("tool_calls", []):
                        
                        tool_name = tool.get("function", {}).get("name")
                        args = json.loads(tool.get("function", {}).get("arguments", "{}"))


                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": f"{selected_server} MCP server {tool_name} call initiated",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        tool_call_result = await call_and_execute_tool(selected_server, selected_server_credentials, tool_name, args)

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": f"{selected_server} MCP server {tool_name} call result  : {json.dumps(tool_call_result)}",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        result.Data["executed_tool_calls"].append({
                            "id": tool.get("id"),
                            "name": tool_name,
                            "arguments": args,
                            "result": tool_call_result,
                        })

                        tool_call_content_data = f"Executed tool: {tool_name} and the result is: {json.dumps(tool_call_result)}"
                        client_details["chat_history"].append({
                            "role": "assistant",
                            "content": tool_call_content_data,
                        })

            else:
                # No function call, normal response case
                client_details["prompt"] = f"{temp_prompt}. Available tools: {json.dumps(tool_call_details_arr)}"
                client_details["tools"] = []

                normal_response = await azure_openai_processor(client_details)
                result.Data["total_llm_calls"] += 1
                result.Data["total_tokens"] += normal_response.Data.get("total_tokens", 0)
                result.Data["total_input_tokens"] += normal_response.Data.get("total_input_tokens", 0)
                result.Data["total_output_tokens"] += normal_response.Data.get("total_output_tokens", 0)
                result.Data["final_llm_response"] = normal_response.Data.get("final_llm_response")
                result.Data["llm_responses_arr"].append(normal_response.Data.get("final_llm_response"))

                result.Data["output_type"] = normal_response.Data.get("output_type", "")
                result.Error = normal_response.Error
                result.Status = normal_response.Status

                content = normal_response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("content")
                if not normal_response.Status or (content is not None and content != ""):
                    result.Data["messages"] = normal_response.Data.get("messages", [])
                    for message in normal_response.Data.get("messages", []):
                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": message,
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "MESSAGE"
                            }))
                    return result

                if len(normal_response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("tool_calls", [])) > 0:
                    # Repeat the tool calling loop as in the TS code
                    final_tool_calls = []
                    selected_tools = extracted_result["selectedTools"]
                    parsed_tools = json.loads(temp_tools)
                    for tool_name in selected_tools:
                        matching_tool = next((t for t in parsed_tools if t.get("function", {}).get("name") == tool_name), None)
                        if matching_tool:
                            final_tool_calls.append(matching_tool)

                    client_details["prompt"] = temp_prompt
                    client_details["tools"] = final_tool_calls

                    while True:
                        response = await azure_openai_processor(client_details)
                        if not response.Status:
                            result.Error = response.Error
                            result.Status = response.Status
                            return result

                        result.Data["total_llm_calls"] += 1
                        result.Data["total_tokens"] += response.Data.get("total_tokens", 0)
                        result.Data["total_input_tokens"] += response.Data.get("total_input_tokens", 0)
                        result.Data["total_output_tokens"] += response.Data.get("total_output_tokens", 0)
                        result.Data["final_llm_response"] = response.Data.get("final_llm_response")
                        result.Data["llm_responses_arr"].append(response.Data.get("final_llm_response"))

                        if response.Data.get("output_type") == "text":
                            result.Data["messages"].extend(response.Data.get("messages", []))
                            result.Data["output_type"] = response.Data.get("output_type", "")
                            result.Error = response.Error
                            result.Status = response.Status

                            for message in response.Data.get("messages", []):
                                if streaming_callback and streaming_callback.get("is_stream"):
                                    await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                        "Data": message,
                                        "Error": None,
                                        "Status": True,
                                        "StreamingStatus": "IN-PROGRESS",
                                        "Action": "MESSAGE"
                                    }))
                            return result

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": "Tool Calls Started",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        for tool in response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("tool_calls", []):
                            tool_name = tool.get("function", {}).get("name")
                            args = json.loads(tool.get("function", {}).get("arguments", "{}"))

                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": f"{selected_server} MCP server {tool_name} call initiated",
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "NOTIFICATION"
                                }))

                            tool_call_result = await call_and_execute_tool(selected_server, selected_server_credentials, tool_name, args)

                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": f"{selected_server} MCP server {tool_name} call result  : {json.dumps(tool_call_result)}",
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "NOTIFICATION"
                                }))

                            result.Data["executed_tool_calls"].append({
                                "id": tool.get("id"),
                                "name": tool_name,
                                "arguments": args,
                                "result": tool_call_result,
                            })

                            tool_call_content_data = f"Executed tool: {tool_name} and the result is: {json.dumps(tool_call_result)}"
                            client_details["chat_history"].append({
                                "role": "assistant",
                                "content": tool_call_content_data,
                            })
        
        elif selected_client == "MCP_CLIENT_OPENAI":

            # Initial LLM call
            initial_llm_response = await openai_processor(client_details)
            if not initial_llm_response.Status:
                result.Error = initial_llm_response.Error
                result.Status = initial_llm_response.Status
                return result
            extracted_result = extract_data_from_response(initial_llm_response.Data.get("messages", [{}])[0] if initial_llm_response.Data else "")
            
            result.Data["total_llm_calls"] += 1
            result.Data["total_tokens"] += initial_llm_response.Data.get("total_tokens", 0)
            result.Data["total_input_tokens"] += initial_llm_response.Data.get("total_input_tokens", 0)
            result.Data["total_output_tokens"] += initial_llm_response.Data.get("total_output_tokens", 0)
            result.Data["final_llm_response"] = initial_llm_response.Data.get("final_llm_response")
            result.Data["llm_responses_arr"].append(initial_llm_response.Data.get("final_llm_response"))

            if streaming_callback and streaming_callback.get("is_stream"):
                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                    "Data": "Optimized Token LLM call Successfully Completed",
                    "Error": None,
                    "Status": True,
                    "StreamingStatus": "IN-PROGRESS",
                    "Action": "NOTIFICATION"
                }))
            
            if extracted_result["isFunctionCall"]:
                final_tool_calls = []
                selected_tools = extracted_result["selectedTools"]
                parsed_tools = json.loads(temp_tools)

                for tool_name in selected_tools:
                    matching_tool = next((t for t in parsed_tools if t.get("function", {}).get("name") == tool_name), None)
                    if matching_tool:
                        final_tool_calls.append(matching_tool)

                client_details["prompt"] = temp_prompt
                client_details["tools"] = final_tool_calls
                

                # Loop to handle multiple LLM calls and tool executions
                while True:
                    response = await openai_processor(client_details)
                    if not response.Status:
                        result.Error = response.Error
                        result.Status = response.Status
                        return result

                    result.Data["total_llm_calls"] += 1
                    result.Data["total_tokens"] += response.Data.get("total_tokens", 0)
                    result.Data["total_input_tokens"] += response.Data.get("total_input_tokens", 0)
                    result.Data["total_output_tokens"] += response.Data.get("total_output_tokens", 0)
                    result.Data["final_llm_response"] = response.Data.get("final_llm_response")
                    result.Data["llm_responses_arr"].append(response.Data.get("final_llm_response"))

                    if response.Data.get("output_type") == "text":
                        result.Data["messages"].extend(response.Data.get("messages", []))
                        result.Data["output_type"] = response.Data.get("output_type", "")
                        result.Error = response.Error
                        result.Status = response.Status

                        for message in response.Data.get("messages", []):
                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": message,
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "MESSAGE"
                                }))
                        return result

                    if streaming_callback and streaming_callback.get("is_stream"):
                        await streaming_callback["streamCallbacks"].on_data(json.dumps({
                            "Data": "Tool Calls Started",
                            "Error": None,
                            "Status": True,
                            "StreamingStatus": "IN-PROGRESS",
                            "Action": "NOTIFICATION"
                        }))

                    for tool in response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("tool_calls", []):
                        
                        tool_name = tool.get("function", {}).get("name")
                        args = json.loads(tool.get("function", {}).get("arguments", "{}"))


                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": f"{selected_server} MCP server {tool_name} call initiated",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        tool_call_result = await call_and_execute_tool(selected_server, selected_server_credentials, tool_name, args)

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": f"{selected_server} MCP server {tool_name} call result  : {json.dumps(tool_call_result)}",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        result.Data["executed_tool_calls"].append({
                            "id": tool.get("id"),
                            "name": tool_name,
                            "arguments": args,
                            "result": tool_call_result,
                        })

                        tool_call_content_data = f"Executed tool: {tool_name} and the result is: {json.dumps(tool_call_result)}"
                        client_details["chat_history"].append({
                            "role": "assistant",
                            "content": tool_call_content_data,
                        })

            else:
                # No function call, normal response case
                client_details["prompt"] = f"{temp_prompt}. Available tools: {json.dumps(tool_call_details_arr)}"
                client_details["tools"] = []

                normal_response = await openai_processor(client_details)
                result.Data["total_llm_calls"] += 1
                result.Data["total_tokens"] += normal_response.Data.get("total_tokens", 0)
                result.Data["total_input_tokens"] += normal_response.Data.get("total_input_tokens", 0)
                result.Data["total_output_tokens"] += normal_response.Data.get("total_output_tokens", 0)
                result.Data["final_llm_response"] = normal_response.Data.get("final_llm_response")
                result.Data["llm_responses_arr"].append(normal_response.Data.get("final_llm_response"))

                result.Data["output_type"] = normal_response.Data.get("output_type", "")
                result.Error = normal_response.Error
                result.Status = normal_response.Status

                content = normal_response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("content")
                if not normal_response.Status or (content is not None and content != ""):
                    result.Data["messages"] = normal_response.Data.get("messages", [])
                    for message in normal_response.Data.get("messages", []):
                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": message,
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "MESSAGE"
                            }))
                    return result

                if len(normal_response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("tool_calls", [])) > 0:
                    # Repeat the tool calling loop as in the TS code
                    final_tool_calls = []
                    selected_tools = extracted_result["selectedTools"]
                    parsed_tools = json.loads(temp_tools)
                    for tool_name in selected_tools:
                        matching_tool = next((t for t in parsed_tools if t.get("function", {}).get("name") == tool_name), None)
                        if matching_tool:
                            final_tool_calls.append(matching_tool)

                    client_details["prompt"] = temp_prompt
                    client_details["tools"] = final_tool_calls

                    while True:
                        response = await openai_processor(client_details)
                        if not response.Status:
                            result.Error = response.Error
                            result.Status = response.Status
                            return result

                        result.Data["total_llm_calls"] += 1
                        result.Data["total_tokens"] += response.Data.get("total_tokens", 0)
                        result.Data["total_input_tokens"] += response.Data.get("total_input_tokens", 0)
                        result.Data["total_output_tokens"] += response.Data.get("total_output_tokens", 0)
                        result.Data["final_llm_response"] = response.Data.get("final_llm_response")
                        result.Data["llm_responses_arr"].append(response.Data.get("final_llm_response"))

                        if response.Data.get("output_type") == "text":
                            result.Data["messages"].extend(response.Data.get("messages", []))
                            result.Data["output_type"] = response.Data.get("output_type", "")
                            result.Error = response.Error
                            result.Status = response.Status

                            for message in response.Data.get("messages", []):
                                if streaming_callback and streaming_callback.get("is_stream"):
                                    await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                        "Data": message,
                                        "Error": None,
                                        "Status": True,
                                        "StreamingStatus": "IN-PROGRESS",
                                        "Action": "MESSAGE"
                                    }))
                            return result

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": "Tool Calls Started",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        for tool in response.Data.get("final_llm_response", {}).get("choices", [{}])[0].get("message", {}).get("tool_calls", []):
                            tool_name = tool.get("function", {}).get("name")
                            args = json.loads(tool.get("function", {}).get("arguments", "{}"))

                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": f"{selected_server} MCP server {tool_name} call initiated",
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "NOTIFICATION"
                                }))

                            tool_call_result = await call_and_execute_tool(selected_server, selected_server_credentials, tool_name, args)

                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": f"{selected_server} MCP server {tool_name} call result  : {json.dumps(tool_call_result)}",
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "NOTIFICATION"
                                }))

                            result.Data["executed_tool_calls"].append({
                                "id": tool.get("id"),
                                "name": tool_name,
                                "arguments": args,
                                "result": tool_call_result,
                            })

                            tool_call_content_data = f"Executed tool: {tool_name} and the result is: {json.dumps(tool_call_result)}"
                            client_details["chat_history"].append({
                                "role": "assistant",
                                "content": tool_call_content_data,
                            })
        
        elif selected_client == "MCP_CLIENT_GEMINI":

            # Initial LLM call
            initial_llm_response = await gemini_processor(client_details)
            print("Initial LLM response:", initial_llm_response)
            if not initial_llm_response.Status:
                result.Error = initial_llm_response.Error
                result.Status = initial_llm_response.Status
                return result
            extracted_result = extract_data_from_response(initial_llm_response.Data.get("messages", [{}])[0] if initial_llm_response.Data else "")
            
            result.Data["total_llm_calls"] += 1
            result.Data["total_tokens"] += initial_llm_response.Data.get("total_tokens", 0)
            result.Data["total_input_tokens"] += initial_llm_response.Data.get("total_input_tokens", 0)
            result.Data["total_output_tokens"] += initial_llm_response.Data.get("total_output_tokens", 0)
            result.Data["final_llm_response"] = initial_llm_response.Data.get("final_llm_response")
            result.Data["llm_responses_arr"].append(initial_llm_response.Data.get("final_llm_response"))

            if streaming_callback and streaming_callback.get("is_stream"):
                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                    "Data": "Optimized Token LLM call Successfully Completed",
                    "Error": None,
                    "Status": True,
                    "StreamingStatus": "IN-PROGRESS",
                    "Action": "NOTIFICATION"
                }))
            
            if extracted_result["isFunctionCall"]:
                final_tool_calls = []
                selected_tools = extracted_result["selectedTools"]
                parsed_tools = json.loads(temp_tools)

                for tool_name in selected_tools:
                    matching_tool = next((t for t in parsed_tools if t.get("function", {}).get("name") == tool_name), None)
                    if matching_tool:
                        final_tool_calls.append(matching_tool)

                client_details["prompt"] = temp_prompt
                client_details["tools"] = final_tool_calls
             

                # Loop to handle multiple LLM calls and tool executions
                count=1
                while True:
                    if count==3:
                        result.Error = "Maximum LLM calls went into halucination"
                        result.Status = response.Status
                        return result
                    
                    if count != 1:
                         client_details["tools"] = []
                    
                    response = await gemini_processor(client_details)
                    print(response)
                    if not response.Status:
                        result.Error = response.Error
                        result.Status = response.Status
                        return result

                    result.Data["total_llm_calls"] += 1
                    result.Data["total_tokens"] += response.Data.get("total_tokens", 0)
                    result.Data["total_input_tokens"] += response.Data.get("total_input_tokens", 0)
                    result.Data["total_output_tokens"] += response.Data.get("total_output_tokens", 0)
                    result.Data["final_llm_response"] = response.Data.get("final_llm_response")
                    result.Data["llm_responses_arr"].append(response.Data.get("final_llm_response"))

                    if response.Data.get("output_type") == "text":
                        result.Data["messages"].extend(response.Data.get("messages", []))
                        result.Data["output_type"] = response.Data.get("output_type", "")
                        result.Error = response.Error
                        result.Status = response.Status

                        for message in response.Data.get("messages", []):
                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": message,
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "MESSAGE"
                                }))
                        return result

                    if streaming_callback and streaming_callback.get("is_stream"):
                        await streaming_callback["streamCallbacks"].on_data(json.dumps({
                            "Data": "Tool Calls Started",
                            "Error": None,
                            "Status": True,
                            "StreamingStatus": "IN-PROGRESS",
                            "Action": "NOTIFICATION"
                        }))

                    final_llm_response = response.Data.get("final_llm_response") if response.Data else None
                    candidates = final_llm_response.get("candidates", []) if final_llm_response else []
                    first_candidate = candidates[0] if candidates and len(candidates) > 0 else {}
                    content = first_candidate.get("content", {}) if isinstance(first_candidate, dict) else {}
                    parts = content.get("parts", []) if isinstance(content, dict) else []

                    for tool in parts:

                        tool_name = tool.get("functionCall", {}).get("name")
                        args_raw = tool.get("functionCall", {}).get("args", {})

                        if isinstance(args_raw, str):
                            try:
                                 args = json.loads(args_raw)
                            except json.JSONDecodeError as e:
                                 args = {}
                        else:
                            args = args_raw

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": f"{selected_server} MCP server {tool_name} call initiated",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        tool_call_result = await call_and_execute_tool(selected_server, selected_server_credentials, tool_name, args)

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": f"{selected_server} MCP server {tool_name} call result  : {json.dumps(tool_call_result)}",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))


                        result.Data["executed_tool_calls"].append({
                            "id": tool.get("id"),
                            "name": tool_name,
                            "arguments": args,
                            "result": tool_call_result,
                        })

                        tool_call_content_data = f"Executed tool: {tool_name} and the result is: {json.dumps(tool_call_result)}"
                        client_details["chat_history"].append({
                            "role": "model",
                            "content": tool_call_content_data,
                        })

                    count+=1
            else:
                # No function call, normal response case
                client_details["prompt"] = f"{temp_prompt}. Available tools: {json.dumps(tool_call_details_arr)}"
                client_details["tools"] = []

                normal_response = await gemini_processor(client_details)
                result.Data["total_llm_calls"] += 1
                result.Data["total_tokens"] += normal_response.Data.get("total_tokens", 0)
                result.Data["total_input_tokens"] += normal_response.Data.get("total_input_tokens", 0)
                result.Data["total_output_tokens"] += normal_response.Data.get("total_output_tokens", 0)
                result.Data["final_llm_response"] = normal_response.Data.get("final_llm_response")
                result.Data["llm_responses_arr"].append(normal_response.Data.get("final_llm_response"))

                result.Data["output_type"] = normal_response.Data.get("output_type", "")
                result.Error = normal_response.Error
                result.Status = normal_response.Status

                final_llm_response = normal_response.Data.get("final_llm_response") if normal_response.Data else None
                candidates = final_llm_response.get("candidates", []) if final_llm_response else []
                first_candidate = candidates[0] if candidates and len(candidates) > 0 else {}
                content = first_candidate.get("content", {}) if isinstance(first_candidate, dict) else {}
                parts = content.get("parts", []) if isinstance(content, dict) else []

                text_content = content.get("text")

                if not normal_response.Status or (text_content is not None and text_content != ""):
                    result.Data["messages"] = normal_response.Data.get("messages", [])
                    for message in normal_response.Data.get("messages", []):
                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": message,
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "MESSAGE"
                            }))
                    return result

                if len(parts) > 0:
                    # Repeat the tool calling loop as in the TS code
                    final_tool_calls = []
                    selected_tools = extracted_result["selectedTools"]
                    parsed_tools = json.loads(temp_tools)
                    for tool_name in selected_tools:
                        matching_tool = next((t for t in parsed_tools if t.get("function", {}).get("name") == tool_name), None)
                        if matching_tool:
                            final_tool_calls.append(matching_tool)

                    client_details["prompt"] = temp_prompt
                    client_details["tools"] = final_tool_calls

                    count=1
                    while True:
                        if count==3:
                            result.Error = "Maximum LLM calls went into halucination"
                            result.Status = False
                            return result
                    
                        if count != 1:
                            client_details["tools"] = []

                        response = await gemini_processor(client_details)
                        if not response.Status:
                            result.Error = response.Error
                            result.Status = response.Status
                            return result

                        result.Data["total_llm_calls"] += 1
                        result.Data["total_tokens"] += response.Data.get("total_tokens", 0)
                        result.Data["total_input_tokens"] += response.Data.get("total_input_tokens", 0)
                        result.Data["total_output_tokens"] += response.Data.get("total_output_tokens", 0)
                        result.Data["final_llm_response"] = response.Data.get("final_llm_response")
                        result.Data["llm_responses_arr"].append(response.Data.get("final_llm_response"))

                        if response.Data.get("output_type") == "text":
                            result.Data["messages"].extend(response.Data.get("messages", []))
                            result.Data["output_type"] = response.Data.get("output_type", "")
                            result.Error = response.Error
                            result.Status = response.Status

                            for message in response.Data.get("messages", []):
                                if streaming_callback and streaming_callback.get("is_stream"):
                                    await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                        "Data": message,
                                        "Error": None,
                                        "Status": True,
                                        "StreamingStatus": "IN-PROGRESS",
                                        "Action": "MESSAGE"
                                    }))
                            return result

                        if streaming_callback and streaming_callback.get("is_stream"):
                            await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                "Data": "Tool Calls Started",
                                "Error": None,
                                "Status": True,
                                "StreamingStatus": "IN-PROGRESS",
                                "Action": "NOTIFICATION"
                            }))

                        final_llm_response = response.Data.get("final_llm_response") if response.Data else None
                        candidates = final_llm_response.get("candidates", []) if final_llm_response else []
                        first_candidate = candidates[0] if candidates and len(candidates) > 0 else {}
                        content = first_candidate.get("content", {}) if isinstance(first_candidate, dict) else {}
                        parts = content.get("parts", []) if isinstance(content, dict) else []

                        for tool in parts:

                            tool_name = tool.get("functionCall", {}).get("name")
                            args_raw = tool.get("functionCall", {}).get("args", {})

                            if isinstance(args_raw, str):
                                try:
                                    args = json.loads(args_raw)
                                except json.JSONDecodeError as e:
                                    args = {}
                            else:
                                args = args_raw

                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": f"{selected_server} MCP server {tool_name} call initiated",
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "NOTIFICATION"
                                }))

                            tool_call_result = await call_and_execute_tool(selected_server, selected_server_credentials, tool_name, args)

                            if streaming_callback and streaming_callback.get("is_stream"):
                                await streaming_callback["streamCallbacks"].on_data(json.dumps({
                                    "Data": f"{selected_server} MCP server {tool_name} call result  : {json.dumps(tool_call_result)}",
                                    "Error": None,
                                    "Status": True,
                                    "StreamingStatus": "IN-PROGRESS",
                                    "Action": "NOTIFICATION"
                                }))


                            result.Data["executed_tool_calls"].append({
                                "id": tool.get("id"),
                                "name": tool_name,
                                "arguments": args,
                                "result": tool_call_result,
                            })

                            tool_call_content_data = f"Executed tool: {tool_name} and the result is: {json.dumps(tool_call_result)}"
                            client_details["chat_history"].append({
                                "role": "model",
                                "content": tool_call_content_data,
                            })

                        count+=1    

        result.Status = True
        return result

    except Exception as e:
        logging.error(f"Exception in client_and_server_execution: {e}")
        res = ClientAndServerExecutionResponse()
        res.Error = str(e)
        res.Status = False
        return res


def extract_data_from_response(message: Any) -> Dict[str, Any]:

    """Parse message content for function call info and selected tools."""
    if not message:
        return {"isFunctionCall": False, "selectedTools": []}

    content =message
    is_function_call = False
    selected_tools = []

    # Parse the content based on your <function_call>TRUE/FALSE</function_call> etc. format
    # Simplified example:
    if "<function_call>TRUE</function_call>" in content:
        is_function_call = True
        start = content.find("<selected_tools>") + len("<selected_tools>")
        end = content.find("</selected_tools>")
        if start != -1 and end != -1:
            tools_str = content[start:end].strip()
            if tools_str.lower() != "none":
                selected_tools = [tool.strip() for tool in tools_str.split(",")]

    return {
        "isFunctionCall": is_function_call,
        "selectedTools": selected_tools,
    }


async def call_and_execute_tool(
    selected_server: str,
    credentials: Any,
    tool_name: str,
    args: Dict[str, Any]
) -> Any:
    """Call the MCP client tool with args and credentials, with JS-style try/catch
       and JSON-serializable output fallback."""
    if selected_server not in MCPServers:
        raise ValueError(f"Server {selected_server} not found in MCPServers")
    
    # pull per-server creds, defaulting to {}
    creds = credentials.get(selected_server, {})

    # switch/case for injecting creds (Python 3.10+)
    match selected_server:
        case "MCP-GSUITE":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        case "FACEBOOK_MCP":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        case "FACEBOOK_ADS_MCP":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        
        # our mcp
        case "mcp-mermaid":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        case "blender-mcp":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        case "coinstats-mcp":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        case "readwise-mcp":
            args["__credentials__"]   = creds
            args["server_credentials"] = creds
        case _:
            pass

    client = MCPServers[selected_server]

    try:
        # perform the tool call
        raw_result = await client.call_tool(tool_name, args)
        
        # try to JSON-serialize it
        try:
            # this will recurse into __dict__ for any object
            serialized = json.loads(
                json.dumps(raw_result, default=lambda o: getattr(o, "__dict__", str(o)))
            )
            tool_call_result = serialized
        except (TypeError, ValueError):
            # fallback to string
            tool_call_result = str(raw_result)

    except Exception as err:
        # catch any call-tool exception and stringify it
        tool_call_result = str(err)

    return tool_call_result