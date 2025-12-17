# plan-kb KB JSON parsing examples

`prox-mesh plan-kb` parses KB stdout as JSON, but the KB transport may include SSH noise before the JSON (e.g., host-key warnings).

The parser (`_parse_json_from_stdout`) uses this order:
1) Direct parse if trimmed stdout starts with `{` or `[`
2) JSONL scan (last valid JSON line wins)
3) Balanced brace/bracket scan from the end (last complete JSON object/array wins)

If none succeed, it raises `ValueError("KB output was not JSON")`.

## Example inputs and expected result

### 1) Clean JSON

Input:
```text
{"results":[1,2]}
```
Expected:
- Parses to object with `results=[1,2]`

### 2) SSH noise + JSON on last line

Input:
```text
Warning: Permanently added 'proxkb' (ED25519) to the list of known hosts.
{"results":[1,2]}
```
Expected:
- Parses to `{"results":[1,2]}`

### 3) SSH noise containing braces + JSON following (acceptance case)

Input:
```text
Warning: added host key {RSA:abc123}
{"results":[1,2]}
```
Expected:
- Parses to `{"results":[1,2]}` (must not parse the `{RSA:...}` noise)

### 4) Multi-line JSON object

Input:
```text
Some banner line
{
  "results": [1, 2],
  "opsec": {"cloud_safe": true}
}
```
Expected:
- Parses to the JSON object spanning multiple lines

## Quick validation snippet

Run this from the repo root:

```powershell
python -c "import sys; sys.path.insert(0, 'nextgen-mesh/ProxOffensive-LocalMesh/agents'); import prox_mesh; cases=[('{\"results\":[1,2]}', '{\"results\": [1, 2]}'), ('Warning: added host key {RSA:abc123}\\n{\"results\":[1,2]}', '{\"results\": [1, 2]}'), ('banner\\n{\\n  \"results\": [1, 2]\\n}', '{\"results\": [1, 2]}')];\nfor s, _ in cases:\n  obj = prox_mesh._parse_json_from_stdout(s)\n  print(type(obj).__name__, obj.get('results') if isinstance(obj, dict) else obj)"
```

