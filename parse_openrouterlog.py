import openrouter_request_parser
import openrouter_response_parser
from pathlib import Path
import os
import glob
BASE_LOG_DIRS = ['D:\\SteamLibrary\\steamapps\\common\\Skyrim Special Edition\\Data\\skse\\Plugins\\SkyrimNet\\logs', 'D:\\temp\\skyrimnet_logarchive']

#recursively scan folders in BASE_LOG_DIRS for request logs named openrouter_input.log.* and response logs openrouter_output.log.*
requestlogs = []
responselogs = []
for base_log_dir in BASE_LOG_DIRS:
    print(f"Scanning base log directory: {base_log_dir}")
    for filename in glob.glob(f'{base_log_dir}/**/*', recursive=True):
        filename = Path(filename)
        if os.path.isfile(filename):
            print(f"Found log file: {filename}")
            if filename.name.startswith("openrouter_input.log"):
                requestlogs.append(filename)
            elif filename.name.startswith("openrouter_output.log"):
                responselogs.append(filename)

print(f"Found {len(requestlogs)} request logs and {len(responselogs)} response logs")
# for each request log create OpenRouterRequestParser() and run it with run()
for request_log in requestlogs:
    print(f"Processing request log: {request_log}")
    requestparser = openrouter_request_parser.OpenRouterRequestParser(input_log_file=str(request_log))
    requestparser.run()

for response_log in responselogs:
    print(f"Processing response log: {response_log}")
    responseparser = openrouter_response_parser.OpenRouterResponseParser(output_log_file=str(response_log))
    responseparser.run()

