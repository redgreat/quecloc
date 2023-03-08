
class MqttConfig(object):
    """
    object model data format:

    object_model = {
        "event": {
            "event_key": {
                "id": 1,
                "perm": "",
                "struct_info": {
                    "struct_key": {
                        "id": 1
                    }
                }
            }
        },
        "property": {
            "property_key": {
                "id": 1,
                "perm": "",
                "struct_info": {
                    "struct_key": {
                        "id": 1
                    }
                }
            }
        }
    }
    """

    # ROSESYO
    host="nas.wongcw.cn"
    port=1883
    username="wangcw"
    password="Mm19890425"
    topic="EC800M/gpspos"
    keepalive=60