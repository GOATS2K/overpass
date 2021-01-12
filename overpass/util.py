def str_to_bool(s):
    if s == "true":
        return True
    elif s == "false":
        return False
    else:
        raise ValueError(f"{s} is not a valid boolean value")

