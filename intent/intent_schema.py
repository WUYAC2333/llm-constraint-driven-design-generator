# intent_schema.py
"""
Defines the canonical schema for parsed design intents.
Currently used as documentation / future validation reference.
"""
intent_schema = {
    "rooms": [
        {
            "type": "<RoomType_ID>",
            "area": "<RoomArea>",
            "adjacent_to": {
                "<OtherRoomType_ID>": "<connection> <direction>"
            }
        }
    ]
}