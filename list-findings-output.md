# list-findings output Schema

```txt
http://schema.nethserver.org/insights/list-findings-output.json
```

Findings of this cluster, sorted by severity, then by last seen, newest first

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                             |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Allowed               | none                | [list-findings-output.json](insights/list-findings-output.json "open original schema") |

## list-findings output Type

`object` ([list-findings output](list-findings-output.md))

## list-findings output Examples

```json
{
  "findings": [
    {
      "id": "01J8Z1K2M3N4P5Q6R7S8T9V0W1",
      "system_id": "abc123",
      "fingerprint": "9f2b7e1c4a",
      "severity": "high",
      "title": "Repeated connection refused on traefik1",
      "summary": "traefik1 logged 37 connection-refused events in 15 minutes, far above baseline.",
      "suggested_action": "Check whether the upstream service on traefik1 is down or overloaded.",
      "modules": [
        "traefik1"
      ],
      "evidence": [
        "<3> [n1:traefik1:traefik] connection refused to 10.0.0.4:8080"
      ],
      "status": "open",
      "occurrence_count": 1,
      "first_seen": 1754380811000,
      "last_seen": 1754381690000,
      "llm_model": "model",
      "prompt_version": "v1",
      "node_refs": [
        {
          "node_id": 1,
          "fqdn": "node1.example.com"
        }
      ],
      "security": false
    }
  ],
  "error": ""
}
```

# list-findings output Properties

| Property              | Type     | Required | Nullable       | Defined by                                                                                                                                                 |
| :-------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [error](#error)       | `string` | Required | cannot be null | [list-findings output](list-findings-output-properties-error.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/error")       |
| [findings](#findings) | `array`  | Required | cannot be null | [list-findings output](list-findings-output-properties-findings.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings") |

## error

Why the findings could not be read, empty on success

`error`

* is required

* Type: `string`

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-error.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/error")

### error Type

`string`

### error Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value                     | Explanation |
| :------------------------ | :---------- |
| `""`                      |             |
| `"subscription_required"` |             |
| `"server_unauthorized"`   |             |
| `"server_unreachable"`    |             |
| `"server_tls_error"`      |             |
| `"server_error"`          |             |

## findings



`findings`

* is required

* Type: `object[]` ([Details](list-findings-output-properties-findings-items.md))

* cannot be null

* defined in: [list-findings output](list-findings-output-properties-findings.md "http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings")

### findings Type

`object[]` ([Details](list-findings-output-properties-findings-items.md))
