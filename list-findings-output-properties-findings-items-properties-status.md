# Untitled string in list-findings output Schema

```txt
http://schema.nethserver.org/insights/list-findings-output.json#/properties/findings/items/properties/status
```



| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                               |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [list-findings-output.json\*](insights/list-findings-output.json "open original schema") |

## status Type

`string`

## status Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value     | Explanation |
| :-------- | :---------- |
| `"open"`  |             |
| `"stale"` |             |
