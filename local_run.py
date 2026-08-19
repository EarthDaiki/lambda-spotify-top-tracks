import json
import sys

from lambda_function import lambda_handler


def main() -> int:
    response = lambda_handler(
        event={},
        context=None
    )

    print(
        json.dumps(
            response,
            ensure_ascii=False,
            indent=4
        )
    )

    return 0 if response.get("statusCode") == 200 else 1


if __name__ == "__main__":
    sys.exit(main())