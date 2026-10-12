# Untitled string in configure-module input Schema

```txt
http://schema.nethserver.org/insights/configure-module-input.json#/properties/log_level
```

Lowest level of the collector messages written to the journal: info adds one line per window, debug also traces the log stream. If omitted, the current value is kept (initially warning)

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                   |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [configure-module-input.json\*](insights/configure-module-input.json "open original schema") |

## log_level Type

`string`

## log_level Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value       | Explanation |
| :---------- | :---------- |
| `"debug"`   |             |
| `"info"`    |             |
| `"warning"` |             |
| `"error"`   |             |
