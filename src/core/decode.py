import base64


def get_dict_structure(d):
    if isinstance(d, dict):
        return {k: get_dict_structure(v) for k, v in d.items()}
    else:
        return None  # Replace with None or any placeholder


def decode_base64url(encoded_message):
    decoded_message = base64.urlsafe_b64decode(encoded_message).decode("utf-8")
    return decoded_message
