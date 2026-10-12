# Untitled string in list-findings input Schema

```txt
http://schema.nethserver.org/insights/list-findings-input.json#/properties/status
```

Which findings to return. Default open

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                             |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [list-findings-input.json\*](insights/list-findings-input.json "open original schema") |

## status Type

`string`

## status Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value     | Explanation |
| :-------- | :---------- |
| `"open"`  |             |
| `"stale"` |             |
| `"all"`   |             |

## status Default Value

The default value is:

```json
"open"
```
