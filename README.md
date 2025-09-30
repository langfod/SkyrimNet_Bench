Attempt to extract SkyrimNet request/response pairs from SKyrimNet log files.

Goal was to use some of them (mainly the simple ones - mood etc...) to benchmark different LLMs.




First:

`skyrim_prompt_parser.py`

Will create prompt "type" json files and "signatures" for matching the request to a request type.


Then:

`parse_openrouterlog.py`

Change BASE_LOG_DIRS to match game folder.


Should create request/response pairs in data\request and data\response named after the request id.

### Directory Structure Created:
```
data/request/
├── character_profile_update/
├── dialogue_response/          
├── dialogue_speaker_selector/  
├── dynamic_bio_update/
├── evaluate_memory_relevance/
├── evaluate_mood/              
├── gamemaster_action_selector/ 
├── generate_search_query/      
├── memory_builder/
├── mood_evaluator/
├── native_action_selector/     
├── native_dialogue_transformer/
├── player_dialogue/
├── player_dialogue_target_selector/
├── player_thoughts/
└── unknown/                    
```