info_request_mapping = {
    "id": "squad_id",
    "name": "name",
    "tag": "tag",
    "ownerId": "owner_id",
    "ownerName": "owner_name",
    "platform": "platform",
    "created": "created",
    "created_ts": "created_ts",
    "acceptingNewMembers": "accepting_new_members",
    "powerId": "power_id",
    "powerName": "power_name",
    "superpowerId": "superpower_id",
    "superpowerName": "superpower_name",
    "factionId": "faction_id",
    "factionName": "faction_name",
    "deleteAfter": "delete_after",
    "userTags": "user_tags",
    "memberCount": "member_count",
    "onlineCount": "online_count",
    "pendingCount": "pending_count",
    "publicComms": "public_comms",
    "publicCommsOverride": "public_comms_override",
    "publicCommsAvailable": "public_comms_available"
}

news_request_mapping = {
    'id': 'news_id'
}


def perform_mapping(mapping: dict, dict_to_map: dict) -> dict:
    for key in (list(dict_to_map.keys())):
        if key in mapping:
            dict_to_map[mapping[key]] = dict_to_map.pop(key)

    return dict_to_map


def perform_info_mapping(info_data: dict) -> dict:
    return perform_mapping(info_request_mapping, info_data)


def perform_news_mapping(news_data: dict) -> dict:
    return perform_mapping(news_request_mapping, news_data)
