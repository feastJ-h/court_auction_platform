class HwpConversionRequiredError(RuntimeError):
    pass


def convert_hwp_placeholder(file_path: str) -> str:
    raise HwpConversionRequiredError(f"HWP conversion pipeline is not configured yet: {file_path}")
