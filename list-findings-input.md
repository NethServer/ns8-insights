# list-findings input Schema

```txt
http://schema.nethserver.org/insights/list-findings-input.json
```

List the findings of this cluster from the insights server

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                           |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :----------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [list-findings-input.json](insights/list-findings-input.json "open original schema") |

## list-findings input Type

`object` ([list-findings input](list-findings-input.md))

## list-findings input Examples

```json
{
  "status": "open"
}
```

# list-findings input Properties

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                          |
| :---------------- | :------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| [status](#status) | `string` | Optional | cannot be null | [list-findings input](list-findings-input-properties-status.md "http://schema.nethserver.org/insights/list-findings-input.json#/properties/status") |

## status

Which findings to return. Default open

`status`

* is optional

* Type: `string`

* cannot be null

* defined in: [list-findings input](list-findings-input-properties-status.md "http://schema.nethserver.org/insights/list-findings-input.json#/properties/status")

### status Type

`string`

### status Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value     | Explanation |
| :-------- | :---------- |
| `"open"`  |             |
| `"stale"` |             |
| `"all"`   |             |

### status Default Value

The default value is:

```json
"open"
```
