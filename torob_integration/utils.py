from collections.abc import Mapping, Sequence


def extract_error_message(errors) -> str:
    """
    تبدیل ساختار خطای DRF به یک پیام ساده برای TorobAPI.
    """

    if isinstance(errors, str):
        return errors

    if isinstance(errors, Mapping):
        for field_name, value in errors.items():
            message = extract_error_message(value)

            if field_name == "non_field_errors":
                return message

            return f"{field_name}: {message}"

    if isinstance(errors, Sequence) and not isinstance(
        errors,
        (str, bytes),
    ):
        if not errors:
            return "Invalid request."

        return extract_error_message(errors[0])

    return str(errors)
