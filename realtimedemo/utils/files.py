import os
import uuid


def random_path(instance, filename):
    """ Random path generator for uploads, specify this for upload_to= argument of FileFields
    """
    # Split the uuid into two parts so that we won't run into subdirectory count limits. First part has 3 hex chars,
    #  thus 4k possible values.
    uuid_hex = uuid.uuid4().hex
    return os.path.join(uuid_hex[:3], uuid_hex[3:], filename)
