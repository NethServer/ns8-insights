# Untitled string in list-findings output Schema

```txt
http://schema.nethserver.org/insights/list-findings-output.json#/properties/error
```

Why the findings could not be read, empty on success

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                               |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [list-findings-output.json\*](insights/list-findings-output.json "open original schema") |

## error Type

`string`

## error Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value                     | Explanation |
| :------------------------ | :---------- |
| `""`                      |             |
| `"subscription_required"` |             |
| `"server_unauthorized"`   |             |
| `"server_unreachable"`    |             |
| `"server_tls_error"`      |             |
| `"server_error"`          |             |
