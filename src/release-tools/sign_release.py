import argparse
import base64
import json
from pathlib import Path
from cryptography.hazmat.primitives import serialization


def canonical_manifest(obj):
    unsigned = dict(obj)
    unsigned.pop("signature", None)
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--key", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    obj = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    obj.pop("signature", None)

    private_key = serialization.load_pem_private_key(
        Path(args.key).read_bytes(), password=None
    )
    signature = private_key.sign(canonical_manifest(obj))
    obj["signature"] = {
        "algorithm": "Ed25519",
        "keyId": "fpv-uhyliant-production-v1",
        "value": base64.b64encode(signature).decode("ascii"),
    }
    manifest_path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Manifest signed:", manifest_path)


if __name__ == "__main__":
    main()